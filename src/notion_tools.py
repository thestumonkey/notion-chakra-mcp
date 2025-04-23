"""
Basic tools for interacting with Notion API.
"""
from typing import Any, Dict, List, Optional
import os
import json
import logging
from notion_client import AsyncClient, Client
from fastmcp import FastMCP, Context
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from models.notion import Database, Page, Block, SearchResults
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotionClientError(Exception):
    """Custom exception for Notion client errors"""
    def __init__(self, message: str, status_code: int = HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        """Return a structure that n8n will recognize as an error"""
        return {
            "success": False,
            "error": True,
            "message": self.message,
            "status": self.status_code
        }

    def __str__(self):
        return f"{self.message} (Status: {self.status_code})"

# Create a dedicated Notion MCP server
notion_mcp = FastMCP("notion-tools", description="Notion API tools and operations")

def get_notion_client(ctx: Context):
    """Get the Notion client from server state"""
    return ctx.request_context.lifespan_context.notion_client

@notion_mcp.tool()
async def list_databases(ctx: Context) -> List[Dict[str, str]]:
    """List all accessible Notion databases with only title and ID."""
    try:
        client = get_notion_client(ctx)
        response = await client.search(filter={"property": "object", "value": "database"})
        databases = response["results"]
        logger.debug(f"Found {len(databases)} databases")
        if not databases:
            return []
        # Return only the title and ID of each database
        return [{"id": db["id"], "title": db["title"][0]["plain_text"]} for db in databases]
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        error = NotionClientError(f"Failed to list databases: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def get_database(ctx: Context, database_id: str) -> Database:
    """Get details about the structure of a specific Notion database."""
    try:
        client = get_notion_client(ctx)
        response = await client.databases.retrieve(database_id=database_id)
        logger.info(f"Database {database_id} retrieved")
        logger.info(f"Database response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error getting database {database_id}: {e}")
        error = NotionClientError(f"Failed to get database: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def query_database(ctx: Context, 
        database_id: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100
        ) -> SearchResults:
    """Query a database with a specified filter to get content in that database.
    
    Args:
        database_id: The ID of the Notion database to query
        filter: The filter to apply, as a JSON-stringified object
            Example: "filter": {
                        "property": "Due date",
                        "date": {
                        "on_or_after": "2023-02-08"
                        }
                    }
        sorts: A list of dictionaries defining the sorting criteria for the query
            [{ "timestamp": "created_time", "direction": "descending" }]
        start_cursor: A string representing the starting cursor for the query 
    """
    try:
        client = get_notion_client(ctx)
        query_params = {
            "database_id": database_id,
            "page_size": page_size
        }
        
        if filter:
            query_params["filter"] = filter
        # Ensure sorts is a list, even if None
        if sorts:
            query_params["sorts"] = sorts
        if start_cursor:
            query_params["start_cursor"] = start_cursor
            
        response = await client.databases.query(**query_params)
        logger.info(f"Query response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error querying database {database_id}: {e}")
        error = NotionClientError(f"Failed to query database: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def create_database(ctx: Context, parent_id: str = os.getenv("NOTION_ROOT_PAGE_ID"), 
                          title: str = "New Database", properties: Optional[Dict[str, Any]] = None) -> Database:
    """Create a new notion database. Must have a parent ID under which the database will be created 
    but we have a default in the env file.
    property schema https://developers.notion.com/reference/property-schema-object"""
    try:
        client = get_notion_client(ctx)
        logger.info(f"Creating database with parent ID: {parent_id}")
        
        # Start with minimum required structure
        payload = {
            "parent": {
                "type": "page_id",
                "page_id": parent_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ],
            "properties": {
                "Name": {
                    "title": {}
                }
            }
        }
        
        # If additional properties were provided, update the properties dictionary
        if properties:
            payload["properties"].update(properties)
        
        logger.info(f"Database payload: {payload}")
        response = await client.databases.create(**payload)
        logger.info(f"Database created")
        logger.debug(f"Database response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        error = NotionClientError(f"Failed to create database: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def update_database(ctx: Context, database_id: str, properties: Optional[Dict[str, Any]] = None) -> Database:
    """Update an existing notion database.
    property schema https://developers.notion.com/reference/property-schema-object
    example: {
        "properties": {
            "Simple Status": {
                "select": {
                    "options": [
                        { "name": "Active" },
                        { "name": "Done" }
                    ]
                }
            }
        }
    }
    """
    try:
        client = get_notion_client(ctx)
        # Extract the inner properties if we have a double-nested structure
        if isinstance(properties, dict) and "properties" in properties:
            properties = properties["properties"]
            
        response = await client.databases.update(database_id=database_id, **{"properties": properties})
        logger.debug(f"Database response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        error = NotionClientError(f"Failed to update database: {e}", status_code=HTTP_400_BAD_REQUEST)      
        return error.to_dict()

@notion_mcp.tool()
async def get_page(ctx: Context, page_id: str):
    """Get details and content about a specific Notion page"""
    try:
        client = get_notion_client(ctx)
        response = await client.pages.retrieve(page_id=page_id)
        logger.info(f"Page {page_id} retrieved")
        logger.info(f"Page response:\n{json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Error getting page {page_id}: {e}")
        error = NotionClientError(f"Failed to get page: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def create_page(ctx: Context, 
        database_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None
        ) -> Page:
    """Create a new page in a database"""
    try:
        client = get_notion_client(ctx)
        logger.info(f"Creating page in database {database_id}")
        logger.info(f"Page data: {page_data}")
        page_data = {
            "parent": {"database_id": database_id}
        }
        
        if properties:
            page_data["properties"] = properties
        if children:
            page_data["children"] = children
            
        response = await client.pages.create(**page_data)
        return response
    except Exception as e:
        logger.error(f"Error creating page in database {database_id}: {e}")
        error = NotionClientError(f"Failed to create page: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def update_page(ctx: Context, 
        page_id: str,
        properties: Dict[str, Any],
        archived: Optional[bool] = None
        ) -> Page:
    """Update an existing page or database"""
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
        error = NotionClientError(f"Failed to update page: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def get_block_children(ctx: Context, 
        block_id: str,
        start_cursor: Optional[str] = None, 
        page_size: int = 100
        ) -> List[Block]:
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
        error = NotionClientError(f"Failed to get block children: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()

@notion_mcp.tool()
async def search(ctx: Context, 
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100
        ) -> SearchResults:
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
        error = NotionClientError(f"Failed to search: {e}", status_code=HTTP_400_BAD_REQUEST)
        return error.to_dict()
