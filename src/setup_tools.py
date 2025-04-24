"""
Setup tools for the MCP server.
"""

import logging
import json
import os
from typing import List, Dict
from typing import Dict
from fastmcp import FastMCP, Context
from src.common_utils import extract_response
from src.models.notion import Database
from src.notion_tools import list_databases

# from IPython import embed

# Create setup MCP instance
setup_mcp = FastMCP(name="setup-tools", description="Setup tools for the MCP server")

logger = logging.getLogger(__name__)


from pydantic import BaseModel

# def normalize_db_name(name: str) -> str:
#     """
#     Convert a database name to a normalized environment variable name.
#     Example: "Tasks DB" -> "NOTION_DB_TASKS_DB"
#     """
#     # Remove special characters and replace spaces with underscores
#     normalized = re.sub(r'[^\w\s-]', '', name)
#     normalized = re.sub(r'[-\s]+', '_', normalized)
#     # Convert to uppercase and add prefix
#     return f"NOTION_DB_{normalized.upper()}"

async def record_db_index(ctx: Context, index_key: str = "notion.database_index", db_list: List[Database] = None) -> Dict[str, str]:
    """Record Notion database IDs as environment variables.
    
    Returns:
        Dict[str, str]: A dictionary mapping environment variable names to database IDs
    """
    logger.info("recording db index")
    memory_client = ctx.request_context.lifespan_context.memory_client

    index = {}
    for db in db_list:
        logger.info("db: %s, name: %s", db.id, db.plain_text_name())
        name = db.plain_text_name()
        index[name] = db.id
        logger.info("index: %s, %s", name, id)
    
    # if os.getenv("DEBUG_REPL"):
    #     logger.info("DEBUG_REPL is true")
    #     embed()

    memory = f"{index_key}: {json.dumps(index)}"
    try:
        # async with memory_client as client:
            # Use update instead of add_memory for storing with a specific key
            await memory_client.call_tool("save_memory", {"text": "memory"})
            # await memory_client.call_tool("save_memory", {"text": memory})
     
            logger.info("Successfully stored database index in memory")
            
            # # Search for the stored memory
            # memory = await memory_client.call_tool("search_memories", index_key)
            logger.info("Retrieved memory: %s", memory)
    except Exception as e:
        logger.error("Error storing/retrieving database index: %s", e)
        raise
    
    # Record each database ID
    return index

async def record_db_schemas(ctx, schema_prefix: str = "notion.schema", databases: List[Database] = None) -> Dict[str, str]:
    """Record Notion database schemas into memory from a list of databases
    
    Args:
        ctx: The context object containing clients
        schema_prefix: The prefix to use for storing schemas in memory
        databases: List of Database objects to store
        
    Returns:
        Dict containing success status and any errors encountered
    """
    memory_client = ctx.request_context.lifespan_context.memory_client
    results = {"success": True, "errors": []}
    
    try:
        for database in databases:
            schema_key = f"{schema_prefix}.{database.id}"
            # Convert database to dict and store as string
            schema_data = database.model_dump()
            await memory_client.call_tool("update_memory", 
                                          {"key": schema_key,
                                           "data": schema_data})
            logger.info("Recorded schema for database: %s (%s)", database.plain_text_name(), database.id)
    except Exception as e:
        error_msg = f"Failed to record schema for database {database.id}: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
        results["success"] = False
        logger.info("Finished recording database schemas. Success: %s", results["success"])
    return results


async def sync_notion_schemas(ctx, index_key: str = "notion.database_index", schema_prefix: str = "notion.schema") -> Dict[str, str]:
    """Sync Notion database schemas from memory"""
    logger.info("syncing schemas")
    memory_client = ctx.request_context.lifespan_context.memory_client
    index = memory_client.get_memory(index_key)
    logger.info("index: %s", index)
    db_ids = list(index.values())
    return await record_db_schemas(ctx, schema_prefix, db_ids)

async def sync_databases(ctx, index_key: str = "notion.database_index", schema_prefix: str = "notion.schema") -> Dict[str, str]:
    """Sync Notion databases from memory"""
    logger.info("getting clients")
    notion_client = ctx.request_context.lifespan_context.notion_client
    memory_client = ctx.request_context.lifespan_context.memory_client
    response = await list_databases(ctx, include_properties=True)
    # response = extract_response(response)
    data = response
    # logger.debug("data: %s", data)
    databases = [Database.model_validate(db) for db in data]
    index = await record_db_index(ctx, index_key, databases)
    schema_indexes = await record_db_schemas(ctx, schema_prefix, databases)

    # # Record each database ID
    # for db in databases:
    #     db_name = db["title"][0]["plain_text"]
    #     db_id = db["id"]
        
    #     # Generate environment variable name
    #     # env_var = normalize_db_name(db_name)
        
    #     # Update .env file
    #     set_key(env_path, env_var, db_id)
    #     recorded_vars[env_var] = db_id
    #     logger.info(f"Mapped '{db_name}' -> {env_var}")
    
    # return recorded_vars 