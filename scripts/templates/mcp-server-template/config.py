"""
Template server configuration.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename TemplateServerConfig to YourServerConfig
3. Update the configuration fields to match your server's requirements
4. Update the validate() method to check your specific configuration needs
"""

from dataclasses import dataclass
from typing import List
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
    """

    base_url: str | None = None
    api_key: str | None = None

    def validate(self) -> List[ConfigIssue]:
        issues: List[ConfigIssue] = []
        if not self.base_url:
            issues.append(ConfigIssue(field="base_url", message="BASE_URL is required", critical=True))
        if not self.api_key:
            issues.append(ConfigIssue(field="api_key", message="API_KEY is required", critical=True))
        return issues
