"""
Configuration for biomcp-mcp server.

This module defines the server configuration, including validation of required
and optional environment variables.

This server uses multiple optional API keys for enhanced functionality:
- ONCOKB_TOKEN: For OncoKB variant annotations (optional)
- ALPHAGENOME_API_KEY: For AlphaGenome variant data (optional)
- NCI_API_KEY: For NCI Clinical Trials API (optional)
- OPENFDA_API_KEY: For FDA API rate limit increases (optional)
- CBIO_TOKEN: For cBioPortal API authentication (optional)
- CBIO_BASE_URL: For custom cBioPortal instance (optional)

The server can function without any of these keys, but features that depend
on them will be unavailable.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add project root to path for common modules
# biomcp-mcp is nested deeper, so we need to go up more levels
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from common.config import ServerConfig, ConfigIssue
except ImportError:
    # Fallback if common module not available
    class ServerConfig:
        def validate(self):
            return []
    
    class ConfigIssue:
        def __init__(self, field, message, critical=False):
            self.field = field
            self.message = message
            self.critical = critical


@dataclass
class BiomcpConfig(ServerConfig):
    """
    Configuration for biomcp-mcp server.
    
    This server uses multiple optional API keys for enhanced functionality.
    All API keys are optional - the server can function without them, but
    features that depend on specific keys will be unavailable.
    """
    
    # Optional: OncoKB API token for variant annotations
    oncokb_token: Optional[str] = None
    
    # Optional: AlphaGenome API key for variant data
    alphagenome_api_key: Optional[str] = None
    
    # Optional: NCI Clinical Trials API key
    nci_api_key: Optional[str] = None
    
    # Optional: FDA API key (for rate limit increases)
    openfda_api_key: Optional[str] = None
    
    # Optional: cBioPortal API token
    cbio_token: Optional[str] = None
    
    # Optional: cBioPortal base URL (default: https://www.cbioportal.org/api)
    cbio_base_url: Optional[str] = None
    
    # Optional: Offline mode (disable external API calls)
    offline_mode: bool = False
    
    # Optional: Cache TTL in hours (default: 24)
    cache_ttl_hours: Optional[int] = None
    
    # Optional: Enable strict output validation
    strict_output_validation: bool = False
    
    # Optional: Use connection pooling
    use_connection_pool: bool = True
    
    # Optional: Metrics enabled
    metrics_enabled: bool = False
    
    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
        """
        issues: List[ConfigIssue] = []
        
        # Validate cBioPortal base URL if provided
        if self.cbio_base_url:
            if not self.cbio_base_url.startswith(("http://", "https://")):
                issues.append(ConfigIssue(
                    field="CBIO_BASE_URL",
                    message="CBIO_BASE_URL must start with http:// or https://",
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
        
        # Note: All API keys are optional, so we don't validate their presence
        # Individual features will handle missing keys gracefully
        
        return issues


def load_config() -> BiomcpConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        BiomcpConfig instance
    """
    return BiomcpConfig(
        oncokb_token=os.getenv("ONCOKB_TOKEN"),
        alphagenome_api_key=os.getenv("ALPHAGENOME_API_KEY"),
        nci_api_key=os.getenv("NCI_API_KEY"),
        openfda_api_key=os.getenv("OPENFDA_API_KEY"),
        cbio_token=os.getenv("CBIO_TOKEN"),
        cbio_base_url=os.getenv("CBIO_BASE_URL", "https://www.cbioportal.org/api"),
        offline_mode=os.getenv("BIOMCP_OFFLINE", "false").lower() in ("true", "1", "yes", "on"),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")) if os.getenv("CACHE_TTL_HOURS") else None,
        strict_output_validation=os.getenv("MCP_STRICT_OUTPUT_VALIDATION", "false").lower() in ("true", "1", "yes", "on"),
        use_connection_pool=os.getenv("BIOMCP_USE_CONNECTION_POOL", "true").lower() in ("true", "1", "yes", "on"),
        metrics_enabled=os.getenv("BIOMCP_METRICS_ENABLED", "false").lower() in ("true", "1", "yes", "on")
    )

