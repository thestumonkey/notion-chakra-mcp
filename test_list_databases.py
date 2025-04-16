"""
Test for listing Notion databases.
"""
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from fastmcp import Client, FastMCP, Context
from fastmcp.client.transports import SSETransport
from contextlib import asynccontextmanager
from notion_client import AsyncClient
import pytest

## Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
if not NOTION_TOKEN:
    raise ValueError("NOTION_API_KEY environment variable is required")

def tool_to_dict(tool):
    """Convert a Tool object to a dictionary"""
    return {
        "name": tool.name,
        "description": tool.description if hasattr(tool, "description") else None,
        "parameters": tool.parameters if hasattr(tool, "parameters") else None
    }

async def test_list_databases():
    """Test the list_databases functionality"""
    try:
        async with Client(SSETransport("http://localhost:8050/sse")) as client:
            # First try to list available tools
            tools = await client.list_tools()
            tools_dict = [tool_to_dict(tool) for tool in tools]
            print("\nAvailable tools:")
            print(json.dumps(tools_dict, indent=2))
            response = await client.call_tool("test_tool", {})
            # Then try to call the specific tool
            response = await client.call_tool("notion_list_databases", {})
            print("\nResponse:")
            print(response)
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
        raise

@pytest.mark.asyncio
class TestNotionTools:
    
    async def test_list_databases(self, get_mcp_client):
        """Test listing all accessible Notion databases"""
        client = get_mcp_client
        response = await client.invoke("notion_mcp.list_databases")
        assert isinstance(response, list)
        if len(response) > 0:
            assert "id" in response[0]
            assert "title" in response[0]
    
    async def test_get_database(self, get_mcp_client):
        """Test getting details about a specific database"""
        client = get_mcp_client
        # First get a database ID from list_databases
        databases = await client.invoke("notion_mcp.list_databases")
        if not databases:
            pytest.skip("No databases available for testing")
        
        database_id = databases[0]["id"]
        response = await client.invoke("notion_mcp.get_database", database_id=database_id)
        assert isinstance(response, dict)
        assert "id" in response
        assert response["id"] == database_id
    
    async def test_query_database(self, get_mcp_client):
        """Test querying items from a database"""
        client = get_mcp_client
        databases = await client.invoke("notion_mcp.list_databases")
        if not databases:
            pytest.skip("No databases available for testing")
        
        database_id = databases[0]["id"]
        response = await client.invoke(
            "notion_mcp.query_database",
            database_id=database_id,
            page_size=10
        )
        assert isinstance(response, dict)
        assert "results" in response
        assert isinstance(response["results"], list)
    
    async def test_create_and_update_page(self, get_mcp_client):
        """Test creating and updating a page in a database"""
        client = get_mcp_client
        databases = await client.invoke("notion_mcp.list_databases")
        if not databases:
            pytest.skip("No databases available for testing")
        
        database_id = databases[0]["id"]
        
        # Get database schema to create valid properties
        db_info = await client.invoke("notion_mcp.get_database", database_id=database_id)
        properties = {}
        
        # Create basic properties based on schema
        for prop_name, prop_schema in db_info["properties"].items():
            if prop_schema["type"] == "title":
                properties[prop_name] = {"title": [{"text": {"content": "Test Page"}}]}
            elif prop_schema["type"] == "rich_text":
                properties[prop_name] = {"rich_text": [{"text": {"content": "Test Content"}}]}
        
        # Create page
        new_page = await client.invoke(
            "notion_mcp.create_page",
            database_id=database_id,
            properties=properties
        )
        assert isinstance(new_page, dict)
        assert "id" in new_page
        
        # Update page
        page_id = new_page["id"]
        updated_properties = properties.copy()
        for prop_name, prop_schema in db_info["properties"].items():
            if prop_schema["type"] == "title":
                updated_properties[prop_name] = {"title": [{"text": {"content": "Updated Test Page"}}]}
        
        updated_page = await client.invoke(
            "notion_mcp.update_page",
            page_id=page_id,
            properties=updated_properties
        )
        assert isinstance(updated_page, dict)
        assert updated_page["id"] == page_id
    
    async def test_get_block_children(self, get_mcp_client):
        """Test getting block children"""
        client = get_mcp_client
        # First create a page with children blocks
        databases = await client.invoke("notion_mcp.list_databases")
        if not databases:
            pytest.skip("No databases available for testing")
        
        database_id = databases[0]["id"]
        db_info = await client.invoke("notion_mcp.get_database", database_id=database_id)
        
        # Create basic properties
        properties = {}
        for prop_name, prop_schema in db_info["properties"].items():
            if prop_schema["type"] == "title":
                properties[prop_name] = {"title": [{"text": {"content": "Test Page with Children"}}]}
        
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Test paragraph"}}]
                }
            }
        ]
        
        # Create page with children
        new_page = await client.invoke(
            "notion_mcp.create_page",
            database_id=database_id,
            properties=properties,
            children=children
        )
        
        # Get children
        response = await client.invoke(
            "notion_mcp.get_block_children",
            block_id=new_page["id"]
        )
        assert isinstance(response, dict)
        assert "results" in response
        assert isinstance(response["results"], list)
        assert len(response["results"]) > 0
    
    async def test_search(self, get_mcp_client):
        """Test searching Notion content"""
        client = get_mcp_client
        response = await client.invoke(
            "notion_mcp.search",
            query="Test",
            page_size=10
        )
        assert isinstance(response, dict)
        assert "results" in response
        assert isinstance(response["results"], list)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_list_databases()) 