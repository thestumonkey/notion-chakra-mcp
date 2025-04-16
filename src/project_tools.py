"""
Project management tools for Notion integration.
"""
import os
import logging
from typing import Optional
from fastmcp import FastMCP, Context

# Configure logging
logger = logging.getLogger(__name__)

# Create Projects MCP server
projects_mcp = FastMCP("projects", description="Project management tools")

@projects_mcp.tool()
async def create_project(
    ctx: Context,
    title: str,
    pillar_id: Optional[str] = None,
    key_result_id: Optional[str] = None,
    status: str = "Not Started",
    priority: str = "P2",
    due_date: Optional[str] = None
) -> str:
    """Create a new project in Notion"""
    try:
        projects_db = os.getenv("NOTION_PROJECTS_DB")
        if not projects_db:
            logger.error("NOTION_PROJECTS_DB environment variable not set")
            return "Error: NOTION_PROJECTS_DB environment variable not set"

        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}},
            "Priority": {"select": {"name": priority}}
        }

        if pillar_id:
            properties["Pillar"] = {"relation": [{"id": pillar_id}]}
        if key_result_id:
            properties["Key Result"] = {"relation": [{"id": key_result_id}]}
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}

        logger.info(f"Creating project: {title}")
        return await ctx.call_tool("notion/create_page", {
            "database_id": projects_db,
            "properties": properties
        })
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        return f"Error creating project: {str(e)}" 