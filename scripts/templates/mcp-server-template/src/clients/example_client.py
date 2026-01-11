"""
Example upstream API client.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename ExampleClient to YourClient
3. Implement actual HTTP calls to your upstream API
4. Add proper error handling using common.errors.map_upstream_error

Replace this with a real client when you create a server from this template.
"""


class ExampleClient:
    """
    Example upstream API client.
    
    Replace this with a real client when you create a server from this template.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def ping(self) -> str:
        # In a real implementation, this would make an HTTP call.
        return "ok"
