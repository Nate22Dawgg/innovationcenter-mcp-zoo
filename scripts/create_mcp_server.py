#!/usr/bin/env python3
"""
MCP Server Scaffolding Script

This script creates a new MCP server from the template by:
1. Prompting for server details (name, domain, description, config vars)
2. Copying the template directory
3. Replacing placeholders with actual values
4. Creating the server structure under servers/<domain>/

Usage:
    python scripts/create_mcp_server.py
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Dict


# Valid domains
VALID_DOMAINS = ["clinical", "markets", "pricing", "claims", "real-estate", "misc"]

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates" / "mcp-server-template"

# Servers root directory
SERVERS_ROOT = Path(__file__).parent.parent / "servers"


def prompt(prompt_text: str, default: str = None, validator=None) -> str:
    """
    Prompt user for input.
    
    Args:
        prompt_text: Text to display
        default: Default value (optional)
        validator: Validation function that returns True if valid (optional)
    
    Returns:
        User input (or default if provided and user presses Enter)
    """
    if default:
        full_prompt = f"{prompt_text} [{default}]: "
    else:
        full_prompt = f"{prompt_text}: "
    
    while True:
        value = input(full_prompt).strip()
        
        if not value and default:
            value = default
        
        if not value:
            print("  Error: This field is required.")
            continue
        
        if validator and not validator(value):
            continue
        
        return value


def validate_server_name(name: str) -> bool:
    """Validate server name format."""
    if not re.match(r'^[a-z0-9-]+-mcp$', name):
        print("  Error: Server name must be lowercase, contain only letters, numbers, and hyphens, and end with '-mcp'")
        print("  Example: biotech-markets-mcp, hospital-prices-mcp")
        return False
    return True


def validate_domain(domain: str) -> bool:
    """Validate domain selection."""
    if domain not in VALID_DOMAINS:
        print(f"  Error: Domain must be one of: {', '.join(VALID_DOMAINS)}")
        return False
    return True


def to_class_name(server_name: str) -> str:
    """Convert server name to class name (e.g., 'biotech-markets-mcp' -> 'BiotechMarketsMcp')."""
    parts = server_name.replace('-mcp', '').split('-')
    return ''.join(word.capitalize() for word in parts) + "ServerConfig"


def to_module_name(server_name: str) -> str:
    """Convert server name to module name (e.g., 'biotech-markets-mcp' -> 'biotech_markets_mcp')."""
    return server_name.replace('-', '_')


def replace_in_file(file_path: Path, replacements: Dict[str, str]) -> None:
    """Replace placeholders in a file."""
    content = file_path.read_text()
    
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    
    file_path.write_text(content)


def update_python_file(file_path: Path, replacements: Dict[str, str]) -> None:
    """Update Python file with replacements, handling both strings and identifiers."""
    content = file_path.read_text()
    
    # Handle identifier replacements (for class names, function names, etc.)
    identifier_replacements = {
        "TemplateServerConfig": replacements.get("CLASS_NAME", "TemplateServerConfig"),
        "template-mcp-server": replacements.get("SERVER_NAME", "template-mcp-server"),
        "example_tool": replacements.get("TOOL_NAME", "example_tool"),
        "ExampleClient": replacements.get("CLIENT_NAME", "ExampleClient"),
        "example": replacements.get("CLIENT_MODULE", "example"),
    }
    
    for old, new in identifier_replacements.items():
        # Replace whole word matches (for identifiers)
        pattern = r'\b' + re.escape(old) + r'\b'
        content = re.sub(pattern, new, content)
    
    # Handle string replacements (for descriptions, env vars, etc.)
    string_replacements = {
        "TEMPLATE_": replacements.get("ENV_PREFIX", "TEMPLATE_"),
        "Template MCP Server": replacements.get("SERVER_DESCRIPTION", "Template MCP Server"),
        "template server": replacements.get("SERVER_DESCRIPTION_LOWER", "template server"),
    }
    
    for old, new in string_replacements.items():
        content = content.replace(old, new)
    
    file_path.write_text(content)


def create_server(
    server_name: str,
    domain: str,
    description: str,
    config_vars: List[str],
    short_description: str
) -> None:
    """
    Create a new MCP server from the template.
    
    Args:
        server_name: Name of the server (e.g., 'biotech-markets-mcp')
        domain: Domain category (e.g., 'clinical', 'markets')
        description: Full description of the server
        config_vars: List of required configuration environment variable names
        short_description: Short description for README
    """
    # Validate inputs
    if not validate_server_name(server_name):
        sys.exit(1)
    
    if not validate_domain(domain):
        sys.exit(1)
    
    # Determine target directory
    target_dir = SERVERS_ROOT / domain / server_name
    
    # Check if directory already exists
    if target_dir.exists():
        response = input(f"\nDirectory {target_dir} already exists. Overwrite? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print(f"Removing existing directory...")
        shutil.rmtree(target_dir)
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nCreating server at: {target_dir}")
    
    # Copy template
    print("Copying template files...")
    shutil.copytree(TEMPLATE_DIR, target_dir, dirs_exist_ok=True)
    
    # Generate replacements
    class_name = to_class_name(server_name)
    module_name = to_module_name(server_name)
    env_prefix = server_name.upper().replace('-', '_')
    
    replacements = {
        "SERVER_NAME": server_name,
        "CLASS_NAME": class_name,
        "MODULE_NAME": module_name,
        "ENV_PREFIX": env_prefix,
        "SERVER_DESCRIPTION": description,
        "SERVER_DESCRIPTION_LOWER": description.lower(),
        "DOMAIN": domain,
        "SHORT_DESCRIPTION": short_description,
    }
    
    # Update files
    print("Updating files with server-specific values...")
    
    # Update config.py
    config_file = target_dir / "config.py"
    if config_file.exists():
        content = config_file.read_text()
        content = content.replace("TemplateServerConfig", class_name)
        content = content.replace("TEMPLATE_", env_prefix + "_")
        config_file.write_text(content)
    
    # Update server.py
    server_file = target_dir / "server.py"
    if server_file.exists():
        content = server_file.read_text()
        content = content.replace("TemplateServerConfig", class_name)
        content = content.replace("template-mcp-server", server_name)
        content = content.replace("TEMPLATE_", env_prefix + "_")
        content = content.replace("Template MCP Server", description)
        server_file.write_text(content)
    
    # Update README.md
    readme_file = target_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        content = content.replace("Template MCP Server", description)
        content = content.replace("template server", description.lower())
        content = content.replace("TEMPLATE_", env_prefix + "_")
        readme_file.write_text(content)
    
    # Update .env.example
    env_example_file = target_dir / ".env.example"
    if env_example_file.exists():
        content = env_example_file.read_text()
        content = content.replace("Template MCP Server", description)
        content = content.replace("TEMPLATE_", env_prefix + "_")
        
        # Replace config vars section
        config_vars_section = "\n".join([
            f"# {var} (required)",
            f"{var}=your-value-here"
            for var in config_vars
        ])
        # Replace the old API_KEY line with new config vars
        old_pattern = "TEMPLATE_API_KEY=your-api-key-here"
        if old_pattern in content:
            content = content.replace(old_pattern, config_vars_section)
        else:
            # If pattern not found, append to end
            content += "\n\n" + config_vars_section
        env_example_file.write_text(content)
    
    # Update __init__.py files if needed
    for init_file in target_dir.rglob("__init__.py"):
        # Keep as-is, just ensure it exists
        pass
    
    print(f"\n✅ Server created successfully at: {target_dir}")
    print("\nNext steps:")
    print(f"  1. Review and update {target_dir}/config.py")
    print(f"  2. Implement your clients in {target_dir}/src/clients/")
    print(f"  3. Implement your tools in {target_dir}/src/tools/")
    print(f"  4. Update {target_dir}/.env.example with your actual config vars")
    print(f"  5. Update tests in {target_dir}/tests/")
    print(f"  6. Run tests: cd {target_dir} && python -m pytest tests/ -v")
    print(f"\n  7. Update registry/tools_registry.json to register your server")
    print(f"     (see docs/REGISTRY_FORMAT.md for details)")


def main():
    """Main entry point."""
    print("=" * 60)
    print("MCP Server Scaffolding Script")
    print("=" * 60)
    print()
    
    # Collect server information
    server_name = prompt(
        "Server name (must end with '-mcp')",
        validator=validate_server_name
    )
    
    print(f"\nAvailable domains: {', '.join(VALID_DOMAINS)}")
    domain = prompt(
        "Domain",
        validator=validate_domain
    )
    
    short_description = prompt(
        "Short description (one line)"
    )
    
    description = prompt(
        "Full description",
        default=short_description
    )
    
    print("\nConfiguration variables:")
    print("  Enter required environment variable names (comma-separated)")
    print("  Example: API_KEY,BASE_URL,API_SECRET")
    config_vars_input = prompt(
        "Required config vars",
        default="API_KEY"
    )
    config_vars = [var.strip().upper() for var in config_vars_input.split(",") if var.strip()]
    
    # Prefix config vars with server name
    env_prefix = server_name.upper().replace('-', '_')
    config_vars = [f"{env_prefix}_{var}" if not var.startswith(env_prefix) else var for var in config_vars]
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Server name: {server_name}")
    print(f"  Domain: {domain}")
    print(f"  Description: {description}")
    print(f"  Config vars: {', '.join(config_vars)}")
    print(f"  Target: servers/{domain}/{server_name}/")
    print("=" * 60)
    
    confirm = prompt("\nCreate server? [Y/n]", default="y")
    if confirm.lower() != 'y' and confirm.lower() != '':
        print("Aborted.")
        sys.exit(0)
    
    # Create the server
    create_server(
        server_name=server_name,
        domain=domain,
        description=description,
        config_vars=config_vars,
        short_description=short_description
    )


if __name__ == "__main__":
    main()
