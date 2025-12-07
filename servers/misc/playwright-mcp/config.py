"""
Playwright MCP Server Configuration

Configuration for the Playwright MCP server with browser settings and safety controls.
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
class PlaywrightServerConfig(ServerConfig):
    """
    Configuration for Playwright MCP server.
    
    Supports browser type selection, headless mode, base URLs for testing,
    and other Playwright-specific settings.
    """
    
    # Browser settings
    browser_type: Optional[str] = None  # chromium, firefox, webkit
    headless: Optional[bool] = True
    browser_timeout: Optional[int] = 30000  # milliseconds
    
    # Base URLs for form submission (optional, for validation)
    base_url: Optional[str] = None
    
    # Safety settings
    default_dry_run: bool = True  # Default to dry-run mode for safety
    
    def validate(self) -> List[ConfigIssue]:
        """
        Validate Playwright server configuration.
        
        Returns:
            List of ConfigIssue objects for any problems found
        """
        issues: List[ConfigIssue] = []
        
        # Validate browser type if provided
        if self.browser_type and self.browser_type not in ["chromium", "firefox", "webkit"]:
            issues.append(ConfigIssue(
                field="browser_type",
                message=f"Invalid browser_type '{self.browser_type}'. Must be one of: chromium, firefox, webkit",
                critical=False  # Non-critical, will default to chromium
            ))
        
        # Validate timeout
        if self.browser_timeout and self.browser_timeout < 1000:
            issues.append(ConfigIssue(
                field="browser_timeout",
                message="browser_timeout must be at least 1000ms",
                critical=False
            ))
        
        # Validate base_url format if provided
        if self.base_url:
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                issues.append(ConfigIssue(
                    field="base_url",
                    message="base_url must start with http:// or https://",
                    critical=False
                ))
        
        return issues
