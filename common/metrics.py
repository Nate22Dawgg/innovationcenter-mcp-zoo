"""
Performance metrics collection for MCP servers.

Provides metrics tracking for cache hit rates, API latency, request counts,
and other performance indicators.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional


@dataclass
class MetricValue:
    """Single metric value with timestamp."""

    value: float
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Thread-safe metrics collector for tracking server performance."""

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        with self._lock:
            metric_key = self._format_key(name, labels)
            self._counters[metric_key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.

        Args:
            name: Gauge name
            value: Gauge value
            labels: Optional labels for the metric
        """
        with self._lock:
            metric_key = self._format_key(name, labels)
            self._gauges[metric_key] = value

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
            labels: Optional labels for the metric
        """
        with self._lock:
            metric_key = self._format_key(name, labels)
            if len(self._histograms[metric_key]) > 1000:
                # Keep only recent 1000 values
                self._histograms[metric_key] = self._histograms[metric_key][-1000:]
            self._histograms[metric_key].append(MetricValue(value, time.time()))

    def record_latency(self, operation: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
        """
        Record operation latency.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            labels: Optional labels
        """
        self.record_histogram(f"{operation}_latency_ms", duration_ms, labels)
        self.increment_counter(f"{operation}_requests", labels=labels)

    def record_cache_hit(self, cache_name: str, hit: bool):
        """
        Record cache hit/miss.

        Args:
            cache_name: Name of the cache
            hit: Whether it was a hit or miss
        """
        self.increment_counter(f"cache_{cache_name}_hits" if hit else f"cache_{cache_name}_misses")

    def record_api_call(
        self,
        api_name: str,
        duration_ms: float,
        status_code: Optional[int] = None,
        error: bool = False,
    ):
        """
        Record an API call.

        Args:
            api_name: Name of the API
            duration_ms: Duration in milliseconds
            status_code: HTTP status code (if applicable)
            error: Whether the call resulted in an error
        """
        labels = {}
        if status_code:
            labels["status_code"] = str(status_code)
        labels["error"] = str(error).lower()

        self.record_latency(f"api_{api_name}", duration_ms, labels)
        self.increment_counter(f"api_{api_name}_calls", labels=labels)
        if error:
            self.increment_counter(f"api_{api_name}_errors", labels=labels)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        with self._lock:
            metric_key = self._format_key(name, labels)
            return self._counters.get(metric_key, 0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value."""
        with self._lock:
            metric_key = self._format_key(name, labels)
            return self._gauges.get(metric_key)

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, float]]:
        """
        Get histogram statistics.

        Returns:
            Dictionary with count, min, max, mean, p50, p95, p99
        """
        with self._lock:
            metric_key = self._format_key(name, labels)
            values = [m.value for m in self._histograms.get(metric_key, [])]
            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": min(sorted_values),
                "max": max(sorted_values),
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.5)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)],
            }

    def get_cache_hit_rate(self, cache_name: str) -> float:
        """
        Get cache hit rate.

        Args:
            cache_name: Name of the cache

        Returns:
            Hit rate as a float between 0 and 1
        """
        hits = self.get_counter(f"cache_{cache_name}_hits")
        misses = self.get_counter(f"cache_{cache_name}_misses")
        total = hits + misses

        if total == 0:
            return 0.0

        return hits / total

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a dictionary format.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            metrics = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
            }

            for name, values in self._histograms.items():
                stats = self.get_histogram_stats(name)
                if stats:
                    metrics["histograms"][name] = stats

            return metrics

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._metrics.clear()

    @staticmethod
    def _format_key(name: str, labels: Optional[Dict[str, str]]) -> str:
        """Format metric key with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

