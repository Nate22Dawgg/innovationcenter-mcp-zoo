"""
Healthcare Equities Orchestrator MCP Server Configuration.

This orchestrator coordinates multiple MCP servers to provide cross-domain analysis
of healthcare companies across markets and clinical domains.
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
class HealthcareEquitiesOrchestratorConfig(ServerConfig):
    """
    Configuration for the Healthcare Equities Orchestrator MCP server.
    
    This orchestrator coordinates calls to multiple upstream MCP servers:
    - biotech-markets-mcp: Company profiles and financials
    - sec-edgar-mcp: SEC filings and company information
    - biomcp-mcp or clinical-trials-mcp: Clinical trial data
    
    Configuration is optional - the orchestrator can work with default settings
    if upstream MCPs are accessible via standard MCP protocol.
    """

    # Optional: Base URLs for upstream MCP servers (if using HTTP transport)
    biotech_markets_mcp_url: Optional[str] = None
    sec_edgar_mcp_url: Optional[str] = None
    clinical_trials_mcp_url: Optional[str] = None
    
    # Optional: Cache TTL settings
    cache_ttl_seconds: int = 300  # Default: 5 minutes

    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
            All configuration is optional - the orchestrator can work with defaults.
        """
        issues: List[ConfigIssue] = []
        
        # All configuration is optional - the orchestrator can work with defaults
        # If URLs are provided, validate they're valid URLs (basic check)
        if self.biotech_markets_mcp_url and not self.biotech_markets_mcp_url.startswith(("http://", "https://")):
            issues.append(ConfigIssue(
                field="biotech_markets_mcp_url",
                message="biotech_markets_mcp_url must start with http:// or https://",
                critical=False  # Non-critical, will use default if invalid
            ))
        
        if self.sec_edgar_mcp_url and not self.sec_edgar_mcp_url.startswith(("http://", "https://")):
            issues.append(ConfigIssue(
                field="sec_edgar_mcp_url",
                message="sec_edgar_mcp_url must start with http:// or https://",
                critical=False
            ))
        
        if self.clinical_trials_mcp_url and not self.clinical_trials_mcp_url.startswith(("http://", "https://")):
            issues.append(ConfigIssue(
                field="clinical_trials_mcp_url",
                message="clinical_trials_mcp_url must start with http:// or https://",
                critical=False
            ))
        
        # Validate cache TTL is reasonable
        if self.cache_ttl_seconds < 0:
            issues.append(ConfigIssue(
                field="cache_ttl_seconds",
                message="cache_ttl_seconds must be non-negative",
                critical=False
            ))
        
        return issues
