"""
Configuration for real-estate-mcp server.

This module defines the server configuration, including validation of required
and optional environment variables for BatchData.io API and other data sources.
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
class RealEstateConfig(ServerConfig):
    """
    Configuration for real-estate-mcp server.
    
    This server uses multiple data sources:
    - BatchData.io (paid, comprehensive) - requires API key
    - County Assessor APIs (free, property tax records)
    - GIS APIs (free, parcel information)
    - Redfin Data Center (free, market trends)
    
    BatchData.io API key is optional but recommended for comprehensive property data.
    The server can function with free sources only, but with limited functionality.
    """
    
    # BatchData.io API configuration
    batchdata_api_key: Optional[str] = None
    batchdata_base_url: Optional[str] = None
    
    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
            Issues marked as critical=True indicate the service cannot function.
        """
        issues: List[ConfigIssue] = []
        
        # BatchData.io API key is optional (fail-soft)
        # The server can function with free sources only
        if not self.batchdata_api_key:
            issues.append(ConfigIssue(
                field="BATCHDATA_API_KEY",
                message="BATCHDATA_API_KEY not set. Some features (comprehensive property lookup) will be unavailable. Free sources (county assessor, GIS, Redfin) will still work.",
                critical=False  # Non-critical: server can function without it
            ))
        elif len(self.batchdata_api_key) < 10:
            issues.append(ConfigIssue(
                field="BATCHDATA_API_KEY",
                message="BATCHDATA_API_KEY appears to be invalid (too short)",
                critical=False  # Warning, not critical
            ))
        
        # Validate base URL if provided
        if self.batchdata_base_url:
            if not self.batchdata_base_url.startswith(("http://", "https://")):
                issues.append(ConfigIssue(
                    field="BATCHDATA_BASE_URL",
                    message="BATCHDATA_BASE_URL must start with http:// or https://",
                    critical=False  # Warning, not critical
                ))
        
        return issues


def load_config() -> RealEstateConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        RealEstateConfig instance
    """
    return RealEstateConfig(
        batchdata_api_key=os.getenv("BATCHDATA_API_KEY"),
        batchdata_base_url=os.getenv("BATCHDATA_BASE_URL", "https://api.batchdata.com/api/v1")
    )
