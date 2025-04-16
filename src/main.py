"""
Main entry point for the Notion MCP server.
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from notion_client import AsyncClient
from collections.abc import AsyncIterator
from fastmcp import FastMCP, Context, Client
from fastmcp.client.transports import (
    SSETransport, 
    PythonStdioTransport, 
    FastMCPTransport
)

# Import MCP servers
from notion_tools import notion_mcp
from project_tools import projects_mcp
from task_tools import tasks_mcp
from okr_tools import okr_mcp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
if not NOTION_TOKEN:
    raise ValueError("NOTION_API_KEY environment variable is required")

@dataclass
class NotionContext:
    """Context for the notion tools server"""
    notion_client: AsyncClient


@asynccontextmanager
async def mcp_lifespan(server: FastMCP) -> AsyncIterator[NotionContext]:
    """Manage the lifecycle of the MCP server and its resources"""
    logger.info("Initializing MCP server resources...")
    
    # Initialize Notion client
    logger.info("Initializing Notion client...")
    notion_client = AsyncClient(auth=NOTION_TOKEN)
    try:
        yield NotionContext(notion_client=notion_client)
    finally:
        logger.info("Cleaning up MCP server resources...")
        # Cleanup Notion client
        if notion_client:
            await notion_client.aclose()
        # Add cleanup for other resources here as needed

# Create main MCP instance
mcp = FastMCP(
    name="notion-chakra-mcp", 
    description="Notion MCP server for personal knowledge and goal management",
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050"),
    lifespan=mcp_lifespan
)

@mcp.tool()
async def test_tool(ctx: Context) -> str:
    """A simple test tool to verify MCP is working"""
    logger.info("Test tool called")
    logger.info("context: %s", ctx)
    logger.info("context server state: %s", ctx.request_context.lifespan_context.notion_client)
    return "Test tool working!"

async def main():
    """Main entry point for the server"""
    logger.info("Starting Notion MCP server...")
    
    # Mount MCP servers
    logger.info("Mounting MCP servers...")
    mcp.mount("notion", notion_mcp)
    mcp.mount("projects", projects_mcp)
    mcp.mount("tasks", tasks_mcp)
    mcp.mount("okr", okr_mcp)
    
    # Start server
    transport = os.getenv("TRANSPORT", "sse")
    logger.info("HOST: %s, PORT: %s", os.getenv("HOST", "0.0.0.0"), os.getenv("PORT", "8050"))
    if transport == 'sse':
        # Run the MCP server with sse transport
        logger.info("Starting MCP server with SSE transport...")
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        logger.info("Starting MCP server with stdio transport...")
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
