"""
Setup tools for the MCP server.
"""
import os
import logging
import re
from dotenv import load_dotenv, set_key
from typing import Dict
from fastmcp import FastMCP, Context
from common_utils import get_mcp_client, extract_response

# Create setup MCP instance
setup_mcp = FastMCP(name="setup-tools", description="Setup tools for the MCP server")

logger = logging.getLogger(__name__)

def normalize_db_name(name: str) -> str:
    """
    Convert a database name to a normalized environment variable name.
    Example: "Tasks DB" -> "NOTION_DB_TASKS_DB"
    """
    # Remove special characters and replace spaces with underscores
    normalized = re.sub(r'[^\w\s-]', '', name)
    normalized = re.sub(r'[-\s]+', '_', normalized)
    # Convert to uppercase and add prefix
    return f"NOTION_DB_{normalized.upper()}"

@setup_mcp.tool()
async def record_dbs(ctx: Context) -> Dict[str, str]:
    """Record Notion database IDs as environment variables.
    
    Returns:
        Dict[str, str]: A dictionary mapping environment variable names to database IDs
    """
    # Create or update .env file
    env_path = ".env"
    if not os.path.exists(env_path):
        open(env_path, "w").close()
    
    # Load existing env vars
    load_dotenv()
    
    recorded_vars = {}
    
    # Get all databases using the notion tool
    async with get_mcp_client() as client:
        response = await client.call_tool("notion_list_databases", {})
        response = extract_response(response)
        databases = response
        
        # Log all database names
        db_names = [db["title"][0]["plain_text"] for db in databases]
        logger.info(f"Found {len(databases)} databases:")
        for name in db_names:
            logger.info(f"  - {name}")
    
    # Record each database ID
    for db in databases:
        db_name = db["title"][0]["plain_text"]
        db_id = db["id"]
        
        # Generate environment variable name
        env_var = normalize_db_name(db_name)
        
        # Update .env file
        set_key(env_path, env_var, db_id)
        recorded_vars[env_var] = db_id
        logger.info(f"Mapped '{db_name}' -> {env_var}")
    
    return recorded_vars 