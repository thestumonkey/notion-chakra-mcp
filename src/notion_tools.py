"""
Basic tools for interacting with Notion API.
"""
from typing import Any, Dict, List, Optional
import os
import json
import logging
from notion_client import AsyncClient
from fastmcp import FastMCP, Context
from tenacity import retry, stop_after_attempt, wait_exponential
from models.notion import Database, SearchResults

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotionClientError(Exception):
    """Custom exception for Notion client errors"""
    pass

# Create a dedicated Notion MCP server
notion_mcp = FastMCP("notion-tools", description="Notion API tools and operations")

def get_notion_client(ctx: Context):
    """Get the Notion client from server state"""
    client = ctx.request_context.get("notion_client")
    if not client:
        raise NotionClientError("Notion client not found in request context")
    return client



@notion_mcp.tool()
async def list_databases(ctx: Context):
    """List all accessible Notion databases"""
    try:
        client = get_notion_client(ctx)
        response = await client.search(filter={"property": "object", "value": "database"})
        databases = response["results"]
        logger.info(f"Databases: {json.dumps(databases[1], indent=2)}")
        if not databases:
            return []
        return [db  for db in databases]
      
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        raise NotionClientError(f"Failed to list databases: {e}")

@notion_mcp.tool()
async def get_database(ctx: Context, database_id: str):
    """Get details about a specific Notion database"""
    try:
        client = get_notion_client(ctx)
        response = await client.databases.retrieve(database_id=database_id)
        return response
    except Exception as e:
        logger.error(f"Error getting database {database_id}: {e}")
        raise NotionClientError(f"Failed to get database: {e}")

@notion_mcp.tool()
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def query_database(ctx: Context, database_id: str, filter: dict = None, sorts: list = None, start_cursor: str = None, page_size: int = 100):
    """Query items from a Notion database"""
    try:
        client = get_notion_client(ctx)
        response = await client.databases.query(
            database_id=database_id,
            filter=filter,
            sorts=sorts,
            start_cursor=start_cursor,
            page_size=page_size
        )
        return response
    except Exception as e:
        logger.error(f"Error querying database {database_id}: {e}")
        raise NotionClientError(f"Failed to query database: {e}")

@notion_mcp.tool()
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def create_page(ctx: Context, database_id: str, properties: dict, children: list = None):
    """Create a new page in a database"""
    try:
        client = get_notion_client(ctx)
        page_data = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        if children:
            page_data["children"] = children
            
        response = await client.pages.create(**page_data)
        return response
    except Exception as e:
        logger.error(f"Error creating page in database {database_id}: {e}")
        raise NotionClientError(f"Failed to create page: {e}")

@notion_mcp.tool()
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def update_page(ctx: Context, page_id: str, properties: dict, archived: bool = False):
    """Update an existing page"""
    try:
        client = get_notion_client(ctx)
        response = await client.pages.update(
            page_id=page_id,
            properties=properties,
            archived=archived
        )
        return response
    except Exception as e:
        logger.error(f"Error updating page {page_id}: {e}")
        raise NotionClientError(f"Failed to update page: {e}")

@notion_mcp.tool()
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_block_children(ctx: Context, block_id: str, start_cursor: str = None, page_size: int = 100):
    """Get the children blocks of a block"""
    try:
        client = get_notion_client(ctx)
        response = await client.blocks.children.list(
            block_id=block_id,
            start_cursor=start_cursor,
            page_size=page_size
        )
        return response
    except Exception as e:
        logger.error(f"Error getting block children for {block_id}: {e}")
        raise NotionClientError(f"Failed to get block children: {e}")

@notion_mcp.tool()
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def search(ctx: Context, query: str = "", filter: dict = None, sort: dict = None, start_cursor: str = None, page_size: int = 100):
    """Search Notion content"""
    try:
        client = get_notion_client(ctx)
        response = await client.search(
            query=query,
            filter=filter,
            sort=sort,
            start_cursor=start_cursor,
            page_size=page_size
        )
        return response
    except Exception as e:
        logger.error(f"Error searching Notion: {e}")
        raise NotionClientError(f"Failed to search: {e}")
