#!/usr/bin/env python3
"""
Sync external MCP servers from GitHub repositories.

This script:
- Clones or updates MCP server repositories from GitHub
- Updates the tools registry with external sources
- Places cloned repos in servers/misc/ or appropriate domain folders

Usage:
    python scripts/sync_github_mcps.py [--dry-run] [--update-existing]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def clone_repo(github_url: str, target_path: Path, dry_run: bool = False) -> bool:
    """
    Clone a GitHub repository to the target path.
    
    Args:
        github_url: GitHub repository URL (e.g., 'user/repo' or full URL)
        target_path: Where to clone the repository
        dry_run: If True, only print what would be done
    
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would clone {github_url} to {target_path}")
        return True
    
    # Convert user/repo format to full URL if needed
    if not github_url.startswith("http"):
        github_url = f"https://github.com/{github_url}.git"
    
    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clone the repository
    try:
        if target_path.exists():
            print(f"  Directory {target_path} already exists. Use --update-existing to update.")
            return False
        
        print(f"  Cloning {github_url}...")
        subprocess.run(
            ["git", "clone", github_url, str(target_path)],
            check=True,
            capture_output=True,
        )
        print(f"  ✓ Cloned to {target_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to clone: {e}", file=sys.stderr)
        return False


def update_repo(target_path: Path, dry_run: bool = False) -> bool:
    """
    Update an existing git repository by pulling latest changes.
    
    Args:
        target_path: Path to the git repository
        dry_run: If True, only print what would be done
    
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would update {target_path}")
        return True
    
    try:
        print(f"  Updating {target_path}...")
        subprocess.run(
            ["git", "-C", str(target_path), "pull"],
            check=True,
            capture_output=True,
        )
        print(f"  ✓ Updated {target_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to update: {e}", file=sys.stderr)
        return False


def sync_external_mcp(
    github_url: str,
    domain: str = "misc",
    update_existing: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Sync a single external MCP from GitHub.
    
    Args:
        github_url: GitHub repository URL or user/repo format
        domain: Domain folder to place the repo in (default: 'misc')
        update_existing: If True, update existing repos instead of skipping
        dry_run: If True, only print what would be done
    
    Returns:
        True if successful, False otherwise
    """
    repo_root = Path(__file__).parent.parent
    
    # Extract repo name from URL
    if "/" in github_url:
        repo_name = github_url.split("/")[-1].replace(".git", "")
    else:
        repo_name = github_url.split("/")[-1]
    
    target_path = repo_root / "servers" / domain / repo_name
    
    print(f"\nSyncing {github_url}...")
    
    # Check if already exists
    if target_path.exists():
        if update_existing:
            return update_repo(target_path, dry_run=dry_run)
        else:
            print(f"  ⚠️  Repository already exists at {target_path}")
            print(f"     Use --update-existing to update")
            return False
    else:
        return clone_repo(github_url, target_path, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="Sync external MCP servers from GitHub"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Update existing repositories instead of skipping them",
    )
    parser.add_argument(
        "repos",
        nargs="*",
        help="GitHub repository URLs or user/repo format (e.g., 'user/repo-name')",
    )
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    # TODO: Load list of external MCPs from a config file or registry
    # For now, this is a stub that demonstrates the structure
    
    if not args.repos:
        print("No repositories specified.")
        print("\nUsage example:")
        print("  python scripts/sync_github_mcps.py user/repo-name")
        print("  python scripts/sync_github_mcps.py --update-existing user/repo-name")
        print("\nTODO: Add configuration file to define external MCP repositories")
        return
    
    success_count = 0
    for repo in args.repos:
        if sync_external_mcp(
            repo,
            domain="misc",
            update_existing=args.update_existing,
            dry_run=args.dry_run,
        ):
            success_count += 1
    
    print(f"\n✅ Synced {success_count}/{len(args.repos)} repository(ies)")


if __name__ == "__main__":
    main()

