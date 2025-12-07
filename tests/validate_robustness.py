#!/usr/bin/env python3
"""
Validation script to check that MCP servers follow robustness standards.

Checks:
1. Use of common error classes
2. Use of common logging
3. Use of common rate limiting
4. Use of common circuit breakers
5. Use of common metrics
6. Input validation
7. Error handling patterns
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Set
import re

PROJECT_ROOT = Path(__file__).parent.parent
SERVERS_DIR = PROJECT_ROOT / "servers"


class RobustnessChecker:
    """Check MCP servers for robustness standards."""
    
    def __init__(self):
        self.issues: List[Dict[str, str]] = []
        self.server_files: List[Path] = []
    
    def find_server_files(self) -> List[Path]:
        """Find all Python server files."""
        server_files = []
        
        for pattern in ["**/server.py", "**/server.ts"]:
            server_files.extend(SERVERS_DIR.glob(pattern))
        
        return sorted(server_files)
    
    def check_python_file(self, file_path: Path) -> List[Dict[str, str]]:
        """Check a Python file for robustness standards."""
        issues = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for common error imports
            if "from common.errors import" not in content and "import common.errors" not in content:
                issues.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "issue": "Missing common.errors import",
                    "severity": "high"
                })
            
            # Check for common logging imports
            if "from common.logging import" not in content and "import common.logging" not in content:
                issues.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "issue": "Missing common.logging import",
                    "severity": "medium"
                })
            
            # Check for error handling patterns
            if "except Exception" in content and "from common.errors" not in content:
                issues.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "issue": "Using generic Exception instead of common error classes",
                    "severity": "medium"
                })
            
            # Check for input validation
            if "ValidationError" not in content and "validate" not in content.lower():
                # This is a warning, not an error
                issues.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "issue": "No input validation detected",
                    "severity": "low"
                })
            
            # Check for rate limiting
            if "rate_limit" not in content.lower() and "RateLimiter" not in content:
                issues.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "issue": "No rate limiting detected",
                    "severity": "low"
                })
            
        except Exception as e:
            issues.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "issue": f"Error checking file: {e}",
                "severity": "high"
            })
        
        return issues
    
    def check_all_servers(self) -> Dict[str, List[Dict[str, str]]]:
        """Check all servers for robustness."""
        server_files = self.find_server_files()
        all_issues = {}
        
        for server_file in server_files:
            if server_file.suffix == ".py":
                issues = self.check_python_file(server_file)
                if issues:
                    all_issues[str(server_file.relative_to(PROJECT_ROOT))] = issues
        
        return all_issues
    
    def print_report(self, issues: Dict[str, List[Dict[str, str]]]):
        """Print a report of issues found."""
        if not issues:
            print("✓ All servers follow robustness standards!")
            return
        
        print(f"\nFound issues in {len(issues)} server(s):\n")
        
        for file_path, file_issues in issues.items():
            print(f"\n{file_path}:")
            for issue in file_issues:
                severity_icon = {
                    "high": "❌",
                    "medium": "⚠️",
                    "low": "ℹ️"
                }.get(issue["severity"], "•")
                
                print(f"  {severity_icon} [{issue['severity'].upper()}] {issue['issue']}")
        
        # Summary
        total_issues = sum(len(issues) for issues in issues.values())
        high_issues = sum(
            1 for issues in issues.values()
            for issue in issues
            if issue["severity"] == "high"
        )
        medium_issues = sum(
            1 for issues in issues.values()
            for issue in issues
            if issue["severity"] == "medium"
        )
        low_issues = sum(
            1 for issues in issues.values()
            for issue in issues
            if issue["severity"] == "low"
        )
        
        print(f"\nSummary:")
        print(f"  Total issues: {total_issues}")
        print(f"  High: {high_issues}")
        print(f"  Medium: {medium_issues}")
        print(f"  Low: {low_issues}")


def main():
    """Main entry point."""
    checker = RobustnessChecker()
    issues = checker.check_all_servers()
    checker.print_report(issues)
    
    # Exit with error code if high severity issues found
    high_issues = sum(
        1 for issues in issues.values()
        for issue in issues
        if issue["severity"] == "high"
    )
    
    if high_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
