"""
Configuration for hospital-prices-mcp server.

This module defines the server configuration, including validation of required
and optional environment variables.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.config import ServerConfig, ConfigIssue


@dataclass
class HospitalPricesConfig(ServerConfig):
    """
    Configuration for hospital-prices-mcp server.
    
    This server requires a Turquoise Health API key to function.
    """
    
    # Required: Turquoise Health API key
    turquoise_api_key: Optional[str] = None
    
    # Optional: Base URL override (for testing or custom endpoints)
    turquoise_base_url: Optional[str] = None
    
    # Optional: Cache TTL in hours (default: 24)
    cache_ttl_hours: Optional[int] = None
    
    # Optional: Enable strict output validation
    strict_output_validation: bool = False
    
    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
        """
        issues: List[ConfigIssue] = []
        
        # API key is required for this service to function
        if not self.turquoise_api_key:
            issues.append(ConfigIssue(
                field="TURQUOISE_API_KEY",
                message="TURQUOISE_API_KEY is required for this service. The service cannot function without this key.",
                critical=True
            ))
        elif len(self.turquoise_api_key.strip()) < 10:
            issues.append(ConfigIssue(
                field="TURQUOISE_API_KEY",
                message="TURQUOISE_API_KEY appears to be invalid (too short)",
                critical=True
            ))
        
        # Validate base URL if provided
        if self.turquoise_base_url:
            if not self.turquoise_base_url.startswith(("http://", "https://")):
                issues.append(ConfigIssue(
                    field="TURQUOISE_BASE_URL",
                    message="TURQUOISE_BASE_URL must start with http:// or https://",
                    critical=False
                ))
        
        # Validate cache TTL if provided
        if self.cache_ttl_hours is not None:
            if self.cache_ttl_hours < 1:
                issues.append(ConfigIssue(
                    field="CACHE_TTL_HOURS",
                    message="CACHE_TTL_HOURS must be at least 1 hour",
                    critical=False
                ))
            elif self.cache_ttl_hours > 8760:  # 1 year
                issues.append(ConfigIssue(
                    field="CACHE_TTL_HOURS",
                    message="CACHE_TTL_HOURS is very large (>1 year), consider a shorter TTL",
                    critical=False
                ))
        
        return issues


def load_config() -> HospitalPricesConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        HospitalPricesConfig instance
    """
    return HospitalPricesConfig(
        turquoise_api_key=os.getenv("TURQUOISE_API_KEY"),
        turquoise_base_url=os.getenv("TURQUOISE_BASE_URL"),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")) if os.getenv("CACHE_TTL_HOURS") else None,
        strict_output_validation=os.getenv("MCP_STRICT_OUTPUT_VALIDATION", "false").lower() in ("true", "1", "yes", "on")
    )
