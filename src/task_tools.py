"""
Task management tools for Notion integration.
"""
import os
import logging
from typing import Optional
from fastmcp import FastMCP, Context

# Configure logging
logger = logging.getLogger(__name__)

# Create Tasks MCP server
tasks_mcp = FastMCP("tasks", description="Task management tools")

@tasks_mcp.tool()
async def create_task(
    ctx: Context,
    title: str,
    project_id: Optional[str] = None,
    status: str = "Not Started",
    priority: str = "P2",
    due_date: Optional[str] = None
) -> str:
    """Create a new task in Notion"""
    try:
        tasks_db = os.getenv("NOTION_TASKS_DB")
        if not tasks_db:
            logger.error("NOTION_TASKS_DB environment variable not set")
            return "Error: NOTION_TASKS_DB environment variable not set"

        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}},
            "Priority": {"select": {"name": priority}}
        }

        if project_id:
            properties["Project"] = {"relation": [{"id": project_id}]}
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}

        logger.info(f"Creating task: {title}")
        return await ctx.call_tool("notion/create_page", {
            "database_id": tasks_db,
            "properties": properties
        })
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        return f"Error creating task: {str(e)}" 