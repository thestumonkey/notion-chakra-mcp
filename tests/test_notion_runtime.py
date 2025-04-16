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

    client = Client(SSETransport(url) if transport == 'sse' else PythonStdioTransport('../main.py'))
    return client  # Let the test handle the async context

@pytest.mark.asyncio
class TestNotionTools:
    """Test cases for Notion tools"""

    async def test_list_databases(self, get_mcp_client):
        """Test listing all accessible Notion databases"""
        async with get_mcp_client as client:
            response = await client.call_tool("notion_list_databases", {})
            response = extract_response(response)
            assert isinstance(response, list)
            if len(response) > 0:
                assert "id" in response[0]
    
    async def test_get_database(self, get_mcp_client):
        """Test getting details about a specific database"""
        async with get_mcp_client as client:
            # First get a database ID from list_databases
            response = await client.call_tool("notion_list_databases", {})
            response = extract_response(response)
            if len(response) > 0:
                database_id = response[0]["id"]
                db_response = await client.call_tool(
                    "notion_get_database",
                    {"database_id": database_id}
                )
                db_response = extract_response(db_response)
                assert "id" in db_response
                assert db_response["id"] == database_id
    
    async def test_query_database(self, get_mcp_client):
        """Test querying items from a database"""
        async with get_mcp_client as client:
            response = await client.call_tool("notion_list_databases", {})
            response = extract_response(response)
            if len(response) > 0:
                database_id = response[0]["id"]
                query_response = await client.call_tool(
                    "notion_query_database",
                    {
                        "database_id": database_id,
                        "page_size": 10,
                        "sorts": []
                    }
                )
                query_response = extract_response(query_response)
                assert "results" in query_response
                assert isinstance(query_response["results"], list)

    async def test_get_page(self, get_mcp_client):
        """Test getting details about a specific page"""
        async with get_mcp_client as client:
            response = await client.call_tool("notion_list_databases", {})
            response = extract_response(response)
            if len(response) > 0:
                database_id = response[0]["id"]
                page_response = await client.call_tool(
                    "notion_get_page",
                    {"page_id": page_id}
                )
                page_response = extract_response(page_response)
                assert "id" in page_response

    @pytest.mark.skip(reason="Skipping test that creates content")
    async def test_create_and_update_page(self, get_mcp_client):
        """Test creating and updating a page in a database"""
        async with get_mcp_client as client:
            response = await client.call_tool("notion_list_databases", {})
            response = extract_response(response)
            if len(response) > 0:
                database_id = response[0]["id"]
                
                # Create a test page
                properties = {
                    "Name": {"title": [{"text": {"content": "Test Page"}}]},
                    
                }
                create_response = await client.call_tool(
                    "notion_create_page",
                    {
                        "database_id": database_id,
                        "properties": properties,
                        "Description": {"rich_text": [{"text": {"content": "Test Description"}}]}
                    }
                )
                create_response = extract_response(create_response)
                assert "id" in create_response
                
                # Update the created page
                page_id = create_response["id"]
                updated_properties = {
                    "Description": {"rich_text": [{"text": {"content": "Updated Description"}}]}
                }
                update_response = await client.call_tool(
                    "notion_update_page",
                    {
                        "page_id": page_id,
                        "properties": updated_properties
                    }
                )
                update_response = extract_response(update_response)
                assert "id" in update_response
                assert update_response["id"] == page_id
    
    @pytest.mark.skip(reason="Skipping test that creates content")
    async def test_get_block_children(self, get_mcp_client):
        """Test getting block children"""
        async with get_mcp_client as client:
            # First create a page with children blocks
            response = await client.call_tool("notion_list_databases", {})
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
                create_response = await client.call_tool(
                    "notion_create_page",
                    {
                        "database_id": database_id,
                        "properties": properties,
                        "children": children
                    }
                )
                create_response = extract_response(create_response)
                
                # Get children blocks of the created page
                page_id = create_response["id"]
                blocks_response = await client.call_tool(
                    "notion_get_block_children",
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
        async with get_mcp_client as client:
            response = await client.call_tool(
                "notion_search",
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