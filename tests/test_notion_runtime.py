import os
import json
import asyncio
import pytest
import pytest_asyncio
from fastmcp import Client
from fastmcp.client.transports import SSETransport, PythonStdioTransport
from mcp.types import TextContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_response(response):
    """Extract the actual response from a FastMCP response that may contain TextContent"""
    if isinstance(response, list) and any(isinstance(item, TextContent) for item in response):
        text_content = next(item for item in response if isinstance(item, TextContent))
        return json.loads(text_content.text)
    return response

@pytest_asyncio.fixture
async def get_mcp_client():
    """Create a FastMCP client connected to the running server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8050"))
    url = f"http://{host}:{port}/sse"
    transport = os.getenv("TRANSPORT", "sse")
    
    if transport == 'sse':
        client = Client(SSETransport(url))
    else:
        client = Client(PythonStdioTransport('../main.py'))
    
    async with client:
        yield client

@pytest.mark.asyncio
class TestNotionTools:
    
    async def test_list_databases(self, get_mcp_client):
        """Test listing all accessible Notion databases"""
        response = await get_mcp_client.call_tool("notion-tools.list_databases", {})
        response = extract_response(response)
        assert isinstance(response, list)
        if len(response) > 0:
            assert "id" in response[0]
    
    async def test_get_database(self, get_mcp_client):
        """Test getting details about a specific database"""
        # First get a database ID from list_databases
        response = await get_mcp_client.call_tool("notion-tools.list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            db_response = await get_mcp_client.call_tool(
                "notion-tools.get_database",
                {"database_id": database_id}
            )
            db_response = extract_response(db_response)
            assert "id" in db_response
            assert db_response["id"] == database_id
    
    async def test_query_database(self, get_mcp_client):
        """Test querying items from a database"""
        response = await get_mcp_client.call_tool("notion-tools.list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            query_response = await get_mcp_client.call_tool(
                "notion-tools.query_database",
                {
                    "database_id": database_id,
                    "page_size": 10
                }
            )
            query_response = extract_response(query_response)
            assert "results" in query_response
            assert isinstance(query_response["results"], list)
    
    async def test_create_and_update_page(self, get_mcp_client):
        """Test creating and updating a page in a database"""
        response = await get_mcp_client.call_tool("notion-tools.list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            
            # Create a test page
            properties = {
                "Name": {"title": [{"text": {"content": "Test Page"}}]},
                "Description": {"rich_text": [{"text": {"content": "Test Description"}}]}
            }
            create_response = await get_mcp_client.call_tool(
                "notion-tools.create_page",
                {
                    "database_id": database_id,
                    "properties": properties
                }
            )
            create_response = extract_response(create_response)
            assert "id" in create_response
            
            # Update the created page
            page_id = create_response["id"]
            updated_properties = {
                "Description": {"rich_text": [{"text": {"content": "Updated Description"}}]}
            }
            update_response = await get_mcp_client.call_tool(
                "notion-tools.update_page",
                {
                    "page_id": page_id,
                    "properties": updated_properties
                }
            )
            update_response = extract_response(update_response)
            assert "id" in update_response
            assert update_response["id"] == page_id
    
    async def test_get_block_children(self, get_mcp_client):
        """Test getting block children"""
        # First create a page with children blocks
        response = await get_mcp_client.call_tool("notion-tools.list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            
            # Create a test page with children blocks
            properties = {
                "Name": {"title": [{"text": {"content": "Test Page with Blocks"}}]},
            }
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "Test paragraph"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "Test heading"}}]
                    }
                }
            ]
            create_response = await get_mcp_client.call_tool(
                "notion-tools.create_page",
                {
                    "database_id": database_id,
                    "properties": properties,
                    "children": children
                }
            )
            create_response = extract_response(create_response)
            
            # Get children blocks of the created page
            page_id = create_response["id"]
            blocks_response = await get_mcp_client.call_tool(
                "notion-tools.get_block_children",
                {
                    "block_id": page_id,
                    "page_size": 10
                }
            )
            blocks_response = extract_response(blocks_response)
            assert "results" in blocks_response
            assert isinstance(blocks_response["results"], list)
            assert len(blocks_response["results"]) == 2
    
    async def test_search(self, get_mcp_client):
        """Test searching Notion content"""
        response = await get_mcp_client.call_tool(
            "notion-tools.search",
            {
                "query": "Test",
                "page_size": 10
            }
        )
        response = extract_response(response)
        assert "results" in response
        assert isinstance(response["results"], list)

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 