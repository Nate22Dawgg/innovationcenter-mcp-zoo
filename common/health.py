"""
Health check utilities for MCP servers.

Provides standardized health check endpoints and status reporting.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .metrics import get_metrics_collector
from .circuit_breaker import get_circuit_breaker_manager


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: float = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }
        if self.message:
            result["message"] = self.message
        if self.details:
            result["details"] = self.details
        return result


class HealthChecker:
    """Manages health checks for an MCP server."""

    def __init__(self, server_name: str):
        """
        Initialize health checker.

        Args:
            server_name: Name of the MCP server
        """
        self.server_name = server_name
        self._checks: List[Callable[[], HealthCheckResult]] = []

    def register_check(self, name: str, check_fn: Callable[[], HealthCheckResult]):
        """
        Register a health check function.

        Args:
            name: Check name
            check_fn: Function that returns HealthCheckResult
        """
        self._checks.append(check_fn)

    def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Health status dictionary
        """
        results = []
        overall_status = HealthStatus.HEALTHY

        for check_fn in self._checks:
            try:
                result = check_fn()
                results.append(result.to_dict())

                # Determine overall status (most severe wins)
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            except Exception as e:
                # Check itself failed
                results.append(
                    HealthCheckResult(
                        name="health_check_error",
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {e}",
                    ).to_dict()
                )
                overall_status = HealthStatus.UNHEALTHY

        return {
            "status": overall_status.value,
            "server": self.server_name,
            "timestamp": time.time(),
            "checks": results,
        }

    def add_basic_checks(self):
        """Add basic health checks (metrics, circuit breakers)."""
        metrics = get_metrics_collector()
        breaker_manager = get_circuit_breaker_manager()

        # Metrics health check
        def check_metrics():
            try:
                metrics_data = metrics.get_all_metrics()
                error_rate = 0.0

                # Calculate overall error rate from counters
                total_requests = sum(
                    v for k, v in metrics_data.get("counters", {}).items() if "requests" in k
                )
                total_errors = sum(
                    v for k, v in metrics_data.get("counters", {}).items() if "errors" in k
                )

                if total_requests > 0:
                    error_rate = total_errors / total_requests

                status = HealthStatus.HEALTHY
                if error_rate > 0.1:  # 10% error rate
                    status = HealthStatus.UNHEALTHY
                elif error_rate > 0.05:  # 5% error rate
                    status = HealthStatus.DEGRADED

                return HealthCheckResult(
                    name="metrics",
                    status=status,
                    details={
                        "error_rate": error_rate,
                        "total_requests": total_requests,
                        "total_errors": total_errors,
                    },
                )
            except Exception as e:
                return HealthCheckResult(
                    name="metrics",
                    status=HealthStatus.DEGRADED,
                    message=f"Failed to check metrics: {e}",
                )

        # Circuit breaker health check
        def check_circuit_breakers():
            try:
                breaker_stats = breaker_manager.get_all_stats()
                open_breakers = [b for b in breaker_stats if b["state"] == "open"]

                status = HealthStatus.HEALTHY
                if open_breakers:
                    status = HealthStatus.DEGRADED if len(open_breakers) < len(breaker_stats) else HealthStatus.UNHEALTHY

                return HealthCheckResult(
                    name="circuit_breakers",
                    status=status,
                    details={
                        "total_breakers": len(breaker_stats),
                        "open_breakers": len(open_breakers),
                        "breakers": breaker_stats,
                    },
                )
            except Exception as e:
                return HealthCheckResult(
                    name="circuit_breakers",
                    status=HealthStatus.DEGRADED,
                    message=f"Failed to check circuit breakers: {e}",
                )

        self.register_check("metrics", check_metrics)
        self.register_check("circuit_breakers", check_circuit_breakers)


def create_health_check_response(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized health check response.

    Args:
        health_data: Health check data from HealthChecker.check_all()

    Returns:
        Standardized health response
    """
    status = health_data["status"]
    http_status = 200

    if status == "unhealthy":
        http_status = 503
    elif status == "degraded":
        http_status = 200  # Still accept requests but indicate degraded

    return {
        "status": status,
        "server": health_data["server"],
        "timestamp": health_data["timestamp"],
        "checks": health_data["checks"],
        "http_status": http_status,
    }

