"""
Configuration for nhanes-mcp server.

This module defines the server configuration, including validation of required
and optional environment variables.

This server accesses NHANES data from local files and does not require
any API keys or authentication for basic operation.
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
class NhanesConfig(ServerConfig):
    """
    Configuration for nhanes-mcp server.
    
    This server accesses NHANES data from local files and does not require
    any API keys or authentication. All configuration options are optional.
    """
    
    # Optional: Data directory path (default: ./data)
    data_directory: Optional[str] = None
    
    # Optional: Config file path (default: ./config/datasets.json)
    config_path: Optional[str] = None
    
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
        
        # Validate data directory if provided
        if self.data_directory:
            data_path = Path(self.data_directory)
            if not data_path.exists():
                issues.append(ConfigIssue(
                    field="NHANES_DATA_DIRECTORY",
                    message=f"NHANES_DATA_DIRECTORY path does not exist: {self.data_directory}",
                    critical=False
                ))
            elif not data_path.is_dir():
                issues.append(ConfigIssue(
                    field="NHANES_DATA_DIRECTORY",
                    message=f"NHANES_DATA_DIRECTORY must be a directory: {self.data_directory}",
                    critical=False
                ))
        
        # Validate config path if provided
        if self.config_path:
            config_file = Path(self.config_path)
            if not config_file.exists():
                issues.append(ConfigIssue(
                    field="NHANES_CONFIG_PATH",
                    message=f"NHANES_CONFIG_PATH file does not exist: {self.config_path}",
                    critical=False
                ))
            elif not config_file.is_file():
                issues.append(ConfigIssue(
                    field="NHANES_CONFIG_PATH",
                    message=f"NHANES_CONFIG_PATH must be a file: {self.config_path}",
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


def load_config() -> NhanesConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        NhanesConfig instance
    """
    # Default paths relative to server.py location
    server_dir = Path(__file__).parent
    default_data_dir = str(server_dir / "data")
    default_config_path = str(server_dir / "config" / "datasets.json")
    
    return NhanesConfig(
        data_directory=os.getenv("NHANES_DATA_DIRECTORY", default_data_dir),
        config_path=os.getenv("NHANES_CONFIG_PATH", default_config_path),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")) if os.getenv("CACHE_TTL_HOURS") else None,
        strict_output_validation=os.getenv("MCP_STRICT_OUTPUT_VALIDATION", "false").lower() in ("true", "1", "yes", "on")
    )

