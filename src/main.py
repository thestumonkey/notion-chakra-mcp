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
    
    # Create task list to track pending operations
    tasks = set()
    server.state.tasks = tasks
    
    try:
        yield NotionContext(notion_client=notion_client)
    finally:
        logger.info("Cleaning up MCP server resources...")
        # Cancel any pending tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for all tasks to complete or be cancelled
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
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
    logger.info("context server state: %s", ctx.request_context.lifespan_context.notion_client)
    return "Test tool working!"

async def cleanup():
    """Cleanup all resources and tasks"""
    logger.info("Starting cleanup process...")
    
    # Get all running tasks
    tasks = asyncio.all_tasks()
    current_task = asyncio.current_task()
    if current_task:
        tasks.remove(current_task)
    
    if tasks:
        logger.info(f"Cancelling {len(tasks)} pending tasks...")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to complete with a timeout
        try:
            await asyncio.wait(tasks, timeout=5.0)
            logger.info("All tasks cancelled successfully")
        except asyncio.TimeoutError:
            logger.warning("Timeout while waiting for tasks to cancel")
    else:
        logger.info("No pending tasks to cleanup")
    
    # Cleanup server state if it exists
    if hasattr(mcp, 'state') and hasattr(mcp.state, 'tasks'):
        logger.info(f"Cleaning up {len(mcp.state.tasks)} tracked server tasks...")
        for task in mcp.state.tasks:
            if not task.done():
                task.cancel()
        if mcp.state.tasks:
            await asyncio.gather(*mcp.state.tasks, return_exceptions=True)
        logger.info("Server tasks cleanup complete")

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
    
    try:
        if transport == 'sse':
            # Run the MCP server with sse transport
            logger.info("Starting MCP server with SSE transport...")
            await mcp.run_sse_async()
        else:
            # Run the MCP server with stdio transport
            logger.info("Starting MCP server with stdio transport...")
            await mcp.run_stdio_async()
    except asyncio.CancelledError:
        logger.info("Received shutdown signal, initiating cleanup...")
        await cleanup()
    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, initiating cleanup...")
        await cleanup()
    finally:
        logger.info("Server shutdown complete")

def handle_sigint():
    """Handle SIGINT (Ctrl+C) gracefully"""
    logger.info("Received SIGINT signal, initiating graceful shutdown...")
    # Get the event loop and create a task to run cleanup
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup())

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Set up signal handlers
        loop.add_signal_handler(signal.SIGINT, handle_sigint)
        loop.add_signal_handler(signal.SIGTERM, handle_sigint)
        
        # Run with more detailed error handling
        try:
            loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"Unexpected error during server execution: {e}", exc_info=True)
            raise
    except KeyboardInterrupt:
        logger.info("Shutdown initiated by keyboard interrupt")
    finally:
        try:
            # Ensure all remaining tasks are cleaned up
            loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
            logger.info("All tasks cleaned up")
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}", exc_info=True)
        finally:
            loop.close()
            logger.info("Event loop closed, shutdown complete")
