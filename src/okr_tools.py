"""
OKR (Objectives and Key Results) tools for Notion integration.
"""
import os
import logging
from typing import Optional
from fastmcp import FastMCP, Context

# Configure logging
logger = logging.getLogger(__name__)

# Create OKR MCP server
okr_mcp = FastMCP("okr", description="OKR management tools")

@okr_mcp.tool()
async def create_pillar(
    ctx: Context,
    title: str,
    description: Optional[str] = None,
    status: str = "Active"
) -> str:
    """Create a new pillar in Notion"""
    try:
        pillars_db = os.getenv("NOTION_PILLARS_DB")
        if not pillars_db:
            logger.error("NOTION_PILLARS_DB environment variable not set")
            return "Error: NOTION_PILLARS_DB environment variable not set"

        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}}
        }

        if description:
            properties["Description"] = {"rich_text": [{"text": {"content": description}}]}

        logger.info(f"Creating pillar: {title}")
        return await ctx.call_tool("notion/create_page", {
            "database_id": pillars_db,
            "properties": properties
        })
    except Exception as e:
        logger.error(f"Error creating pillar: {str(e)}", exc_info=True)
        return f"Error creating pillar: {str(e)}"

@okr_mcp.tool()
async def create_key_result(
    ctx: Context,
    title: str,
    objective_id: str,
    target_value: float,
    current_value: float = 0.0,
    unit: str = "%",
    status: str = "Not Started"
) -> str:
    """Create a new key result in Notion"""
    try:
        kr_db = os.getenv("NOTION_KEY_RESULTS_DB")
        if not kr_db:
            logger.error("NOTION_KEY_RESULTS_DB environment variable not set")
            return "Error: NOTION_KEY_RESULTS_DB environment variable not set"

        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Objective": {"relation": [{"id": objective_id}]},
            "Target Value": {"number": target_value},
            "Current Value": {"number": current_value},
            "Unit": {"select": {"name": unit}},
            "Status": {"select": {"name": status}}
        }

        logger.info(f"Creating key result: {title}")
        return await ctx.call_tool("notion/create_page", {
            "database_id": kr_db,
            "properties": properties
        })
    except Exception as e:
        logger.error(f"Error creating key result: {str(e)}", exc_info=True)
        return f"Error creating key result: {str(e)}" 