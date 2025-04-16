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
import asyncio

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
    return ctx.request_context.lifespan_context.notion_client

@notion_mcp.tool()
async def list_databases(ctx: Context):
    """List all accessible Notion databases"""
    try:
        client = get_notion_client(ctx)
        response = await client.search(filter={"property": "object", "value": "database"})
        databases = response["results"]
        logger.info(f"Found {len(databases)} databases")
        logger.info(f"Databases first response:\n{json.dumps(databases[0], indent=2)}")
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
        logger.info(f"Database {database_id} retrieved")
        logger.info(f"Database response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error getting database {database_id}: {e}")
        raise NotionClientError(f"Failed to get database: {e}")

@notion_mcp.tool()
async def query_database(ctx: Context, database_id: str, filter: dict = None, sorts: list = [], start_cursor: str = None, page_size: int = 100):
    """Query items from a Notion database"""
    try:
        client = get_notion_client(ctx)
        query_params = {
            "database_id": database_id,
            "page_size": page_size
        }
        
        if filter is not None:
            query_params["filter"] = filter
        if sorts:
            query_params["sorts"] = sorts
        if start_cursor:
            query_params["start_cursor"] = start_cursor
            
        response = await client.databases.query(**query_params)
        logger.info(f"Query response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error querying database {database_id}: {e}")
        raise NotionClientError(f"Failed to query database: {e}")

@notion_mcp.tool()
async def get_page(ctx: Context, page_id: str):
    """Get details about a specific Notion page"""
    try:
        client = get_notion_client(ctx)
        response = await client.pages.retrieve(page_id=page_id)
        logger.info(f"Page {page_id} retrieved")
        logger.info(f"Page response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error getting page {page_id}: {e}")
        raise NotionClientError(f"Failed to get page: {e}")

@notion_mcp.tool()
async def create_page(ctx: Context, database_id: str, properties: dict = None, children: list = None):
    """Create a new page in a database"""
    try:
        client = get_notion_client(ctx)
        page_data = {
            "parent": {"database_id": database_id}
        }
        
        if properties is not None:
            page_data["properties"] = properties
        if children is not None:
            page_data["children"] = children
            
        response = await client.pages.create(**page_data)
        return response
    except Exception as e:
        logger.error(f"Error creating page in database {database_id}: {e}")
        raise NotionClientError(f"Failed to create page: {e}")

@notion_mcp.tool()
async def update_page(ctx: Context, page_id: str, properties: dict = None, archived: bool = False):
    """Update an existing page"""
    try:
        client = get_notion_client(ctx)
        update_data = {}
        
        if properties is not None:
            update_data["properties"] = properties
        if archived:
            update_data["archived"] = archived
            
        response = await client.pages.update(
            page_id=page_id,
            **update_data
        )
        return response
    except Exception as e:
        logger.error(f"Error updating page {page_id}: {e}")
        raise NotionClientError(f"Failed to update page: {e}")

@notion_mcp.tool()
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
async def search(ctx: Context, query: str = "", filter: dict = None, sort: dict = None, start_cursor: str = None, page_size: int = 100):
    """Search Notion content"""
    try:
        client = get_notion_client(ctx)
        search_params = {
            "query": query,
            "page_size": page_size
        }
        
        if filter is not None:
            search_params["filter"] = filter
        if sort is not None:
            search_params["sort"] = sort
        if start_cursor:
            search_params["start_cursor"] = start_cursor
            
        response = await client.search(**search_params)
        return response
    except Exception as e:
        logger.error(f"Error searching Notion: {e}")
        raise NotionClientError(f"Failed to search: {e}")
