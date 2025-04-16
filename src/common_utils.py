import os
import json
from fastmcp import Client
from fastmcp.client.transports import SSETransport, PythonStdioTransport
from mcp.types import TextContent

def extract_response(response):
    """Extract the actual response from a FastMCP response that may contain TextContent"""
    if isinstance(response, list) and any(isinstance(item, TextContent) for item in response):
        text_content = next(item for item in response if isinstance(item, TextContent))
        return json.loads(text_content.text)
    return response

def get_mcp_client():
    """Create a FastMCP client connected to the running server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8050"))
    url = f"http://{host}:{port}/sse"
    transport = os.getenv("TRANSPORT", "sse")

    return Client(SSETransport(url) if transport == 'sse' else PythonStdioTransport("src/main.py"))