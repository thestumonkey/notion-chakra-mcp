"""
Schema management tools for Notion integration.
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from fastmcp import FastMCP, Context

from common_utils import get_mcp_client, extract_response
from schemas.schema_manager import SchemaManager

# Configure logging
logger = logging.getLogger(__name__)

# Create Schema MCP server
schema_mcp = FastMCP("schemas", description="Schema management tools")

# @schema_mcp.tool()
async def fetch_schemas(ctx: Context, config_name: str = "default") -> Dict[str, Any]:
    """
    Fetch and store schemas for all accessible Notion databases. Check to see if the schemas have already been fetched
    and stored in the data/schemas directory under the config_name directory. This tool only needs to be used if we're making
    a new config, or if there's an error with creating content so we need to update the schemas.
    
    Args:
        config_name: Name of the configuration to store schemas under
        
    Returns:
        Dict mapping database names to their schemas
    """
    schema_manager = SchemaManager(config_name)
    schemas = {}
    
    try:
        async with get_mcp_client() as client:
            # Get list of databases
            response = await client.call_tool("notion_list_databases", {})
            databases = extract_response(response)
            
            # Log all database names
            db_names = [db["title"][0]["plain_text"] for db in databases]
            logger.info(f"Found {len(databases)} databases for config '{config_name}':")
            for name in db_names:
                logger.info(f"  - {name}")
            
            # Fetch schema for each database
            for db in databases:
                db_id = db["id"]
                response = await client.call_tool(
                    "notion_get_database",
                    {"database_id": db_id}
                )
                db_details = extract_response(response)
                
                # Extract and store schema
                schema = schema_manager.extract_database_schema(db_details)
                db_name = schema["title"]
                schema_manager.save_schema(db_name, schema)
                schemas[db_name] = schema
                
                logger.info(f"Fetched and stored schema for database: {db_name}")
        
        return schemas
    
    except Exception as e:
        logger.error(f"Error fetching database schemas: {e}")
        raise

# @schema_mcp.tool()
async def get_schema(ctx: Context, database_name: str, 
          config_name: Optional[str] = "default") -> Optional[Dict[str, Any]]:
    """
    Get schema for a specific database, fetching from Notion if not cached.
    
    Args:
        database_name: Name of the database to get schema for
        config_name: Name of the configuration to get schema from
        
    Returns:
        Database schema if found, None otherwise
    """
    schema_manager = SchemaManager(config_name)
    
    # Try to load from cache first
    schema = schema_manager.load_schema(database_name)
    if schema:
        return schema
    
    # If not in cache, fetch all schemas (which will cache them)
    schemas = await fetch_schemas(ctx, config_name)
    return schemas.get(database_name)

# @schema_mcp.tool()
async def list_schemas(ctx: Context, 
        config_name: Optional[str] = "default") -> List[str]:
    """
    List all available schemas for a configuration.
    
    Args:
        config_name: Name of the configuration to list schemas for
        
    Returns:
        List of schema names available for the configuration
    """
    schema_manager = SchemaManager(config_name)
    schemas = schema_manager.list_schemas()
    logger.info(f"Found {len(schemas)} schemas for config {config_name}")
    return schemas

# @schema_mcp.tool()
async def list_configs(ctx: Context) -> List[str]:
    """
    List all available schema configurations.
    
    Returns:
        List of configuration names
    """
    configs = SchemaManager.list_configs()
    logger.info(f"Found {len(configs)} schema configurations")
    return configs 