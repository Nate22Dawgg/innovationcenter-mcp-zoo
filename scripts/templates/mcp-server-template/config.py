"""
Template server configuration.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename TemplateServerConfig to YourServerConfig
3. Update the configuration fields to match your server's requirements
4. Update the validate() method to check your specific configuration needs
"""

import os
from dataclasses import dataclass
from typing import List, Optional
import sys
from pathlib import Path

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.config import ServerConfig, ConfigIssue


@dataclass
class TemplateServerConfig(ServerConfig):
    """
    Example server-specific configuration for a new MCP server.
    
    Copy/rename this class when creating a real server.
    Replace the fields below with your server's actual configuration needs.
    
    This demonstrates:
    - Required fields (api_key)
    - Optional fields (base_url with default)
    - Validation logic using ConfigIssue
    """

    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
            Issues marked as critical=True indicate the service cannot function.
        """
        issues: List[ConfigIssue] = []
        
        # Example: base_url is optional with a default
        if not self.base_url:
            # You might want to set a default or make it required
            # This example makes it optional (non-critical)
            issues.append(ConfigIssue(
                field="base_url",
                message="BASE_URL not set, using default",
                critical=False
            ))
            self.base_url = "https://api.example.com"  # Set default
        
        # Example: api_key is required (critical)
        if not self.api_key:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY is required for this service",
                critical=True
            ))
        
        # Example: validate API key format (if applicable)
        if self.api_key and len(self.api_key) < 10:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY appears to be invalid (too short)",
                critical=True
            ))
        
        return issues
