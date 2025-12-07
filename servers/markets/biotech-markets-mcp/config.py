"""
Configuration for biotech-markets-mcp server.

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
class BiotechMarketsConfig(ServerConfig):
    """
    Configuration for biotech-markets-mcp server.
    
    This server uses free public APIs (ClinicalTrials.gov, SEC EDGAR, PubMed)
    and does not require API keys for basic operation. Optional configuration
    can enable additional features or paid data sources.
    """
    
    # Optional: User-Agent for SEC EDGAR API (required by SEC)
    sec_user_agent: Optional[str] = None
    
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
        
        # SEC EDGAR requires a User-Agent header, but we provide a default
        # This is a warning, not critical
        if not self.sec_user_agent:
            issues.append(ConfigIssue(
                field="SEC_USER_AGENT",
                message="SEC_USER_AGENT not set, using default. SEC EDGAR API requires a User-Agent header.",
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


def load_config() -> BiotechMarketsConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        BiotechMarketsConfig instance
    """
    return BiotechMarketsConfig(
        sec_user_agent=os.getenv("SEC_USER_AGENT", "MCP Biotech Markets Server (contact@example.com)"),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")) if os.getenv("CACHE_TTL_HOURS") else None,
        strict_output_validation=os.getenv("MCP_STRICT_OUTPUT_VALIDATION", "false").lower() in ("true", "1", "yes", "on")
    )
