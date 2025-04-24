"""
Main entry point for the Notion MCP server.
"""
import os
import logging
import asyncio
import signal
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
from mcp.server.session import ServerSession
from fastapi import FastAPI
from src.telemetry import setup_telemetry

# Import MCP servers
from src.notion_tools import notion_mcp
from src.setup_tools import sync_databases, sync_notion_schemas
from src.block_tools import block_mcp

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    memory_client: Client

@asynccontextmanager
async def mcp_lifespan(server: FastMCP) -> AsyncIterator[NotionContext]:
    """Manage the lifecycle of the MCP server and its resources"""
    logger.info("Initializing MCP server resources...")
    
    # Initialize Notion client
    logger.info("Initializing Notion client...")
    notion_client = AsyncClient(auth=NOTION_TOKEN)
    notion_logger = logging.getLogger("notion_client")
    async with Client(os.getenv("MEM0_SERVER_URL")) as memory_client:
        try:
            yield NotionContext(notion_client=notion_client, memory_client=memory_client)
        finally:
            logger.info("Cleaning up MCP server resources...")
            # Cleanup Notion client
            if notion_client:
                await notion_client.aclose()
            # Add cleanup for other resources here as needed
            if memory_client:
                memory_client.close()

# Create main MCP instance
mcp = FastMCP(
    name="notion-chakra-mcp", 
    description="Notion MCP server for personal knowledge and goal management",
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8051"),
    lifespan=mcp_lifespan,
    settings={"initialization_timeout": 10.0, "log_level": "DEBUG"}  # 10 second timeout
)

async def cleanup():
    """Cleanup all resources and tasks"""
    logger.info("Starting cleanup process...")
    # Cancel all tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Cleanup complete")

def shutdown(signal_type, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signal_type}")
    # Force exit to avoid threading issues
    os._exit(0)

@mcp.tool()
async def startup(ctx: Context):
    """Startup tasks"""
    logger.info("Starting startup tasks...")
    logger.info("ctx: %s", ctx)
    await sync_databases(ctx)
    await sync_notion_schemas(ctx)
    logger.info("Startup tasks complete")

app = FastAPI()
setup_telemetry(app)

async def main():
    """Main entry point for the server"""
    logger.info("Starting Notion MCP server...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Mount MCP servers
    logger.info("Mounting MCP servers...")
    mcp.mount("notion", notion_mcp)
    mcp.mount("blocks", block_mcp)
    
    # Start server
    transport = os.getenv("TRANSPORT", "sse")
    
    try:
        if transport == 'sse':
            # Run the MCP server with sse transport
            logger.info("Starting MCP server with SSE transport...")
            logger.info("HOST: %s, PORT: %s", os.getenv("HOST", "0.0.0.0"), os.getenv("PORT", "8050"))
            await mcp.run_sse_async()
        else:
            # Run the MCP server with stdio transport
            logger.info("Starting MCP server with stdio transport...")
            await mcp.run_stdio_async()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received...")
    finally:
        await cleanup()
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    try:
        logger.info("Starting main loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        # Force exit to avoid threading issues
        os._exit(0)
