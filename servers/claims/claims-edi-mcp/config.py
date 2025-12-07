"""
Configuration for claims-edi-mcp server.

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
class ClaimsEdiConfig(ServerConfig):
    """
    Configuration for claims-edi-mcp server.
    
    This server processes EDI 837/835 files and looks up CMS fee schedules.
    It does not require external API keys for basic operation, but may have
    optional configuration for enhanced features.
    """
    
    # Optional: CMS fee schedule data directory
    cms_data_directory: Optional[str] = None
    
    # Optional: Cache TTL in hours (default: 24)
    cache_ttl_hours: Optional[int] = None
    
    # Optional: Enable strict output validation
    strict_output_validation: bool = False
    
    # Optional: Enable PHI redaction (default: True)
    enable_phi_redaction: bool = True
    
    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
        """
        issues: List[ConfigIssue] = []
        
        # Validate CMS data directory if provided
        if self.cms_data_directory:
            data_path = Path(self.cms_data_directory)
            if not data_path.exists():
                issues.append(ConfigIssue(
                    field="CMS_DATA_DIRECTORY",
                    message=f"CMS_DATA_DIRECTORY path does not exist: {self.cms_data_directory}",
                    critical=False
                ))
            elif not data_path.is_dir():
                issues.append(ConfigIssue(
                    field="CMS_DATA_DIRECTORY",
                    message=f"CMS_DATA_DIRECTORY must be a directory: {self.cms_data_directory}",
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


def load_config() -> ClaimsEdiConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        ClaimsEdiConfig instance
    """
    return ClaimsEdiConfig(
        cms_data_directory=os.getenv("CMS_DATA_DIRECTORY"),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")) if os.getenv("CACHE_TTL_HOURS") else None,
        strict_output_validation=os.getenv("MCP_STRICT_OUTPUT_VALIDATION", "false").lower() in ("true", "1", "yes", "on"),
        enable_phi_redaction=os.getenv("ENABLE_PHI_REDACTION", "true").lower() in ("true", "1", "yes", "on")
    )
