import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from common_utils import extract_response, get_mcp_client

# Load environment variables
load_dotenv()

@pytest_asyncio.fixture
async def client():
    """Setup MCP client for tests"""
    return get_mcp_client()  # Now returns the client directly, no await needed

@pytest.mark.asyncio
async def test_list_databases(client):
    """Test listing all accessible Notion databases"""
    async with client as c:
        response = await c.call_tool("notion_list_databases", {})
        response = extract_response(response)
        assert isinstance(response, list)
        if len(response) > 0:
            assert "id" in response[0]

@pytest.mark.asyncio
async def test_get_database(client):
    """Test getting details about a specific database"""
    async with client as c:
        # First get a database ID from list_databases
        response = await c.call_tool("notion_list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            db_response = await c.call_tool(
                "notion_get_database",
                {"database_id": database_id}
            )
            db_response = extract_response(db_response)
            assert "id" in db_response
            assert db_response["id"] == database_id

@pytest.mark.asyncio
async def test_query_database(client):
    """Test querying items from a database"""
    async with client as c:
        response = await c.call_tool("notion_list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            query_response = await c.call_tool(
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

@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping test that creates content")
async def test_create_and_update_page(client):
    """Test creating and updating a page in a database"""
    async with client as c:
        response = await c.call_tool("notion_list_databases", {})
        response = extract_response(response)
        if len(response) > 0:
            database_id = response[0]["id"]
            
            # Create a test page
            properties = {
                "Name": {"title": [{"text": {"content": "Test Page"}}]},
            }
            create_response = await c.call_tool(
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
            update_response = await c.call_tool(
                "notion_update_page",
                {
                    "page_id": page_id,
                    "properties": updated_properties
                }
            )
            update_response = extract_response(update_response)
            assert "id" in update_response
            assert update_response["id"] == page_id

@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping test that creates content")
async def test_get_block_children(client):
    """Test getting block children"""
    async with client as c:
        # First create a page with children blocks
        response = await c.call_tool("notion_list_databases", {})
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
            create_response = await c.call_tool(
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
            blocks_response = await c.call_tool(
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

@pytest.mark.asyncio
async def test_search(client):
    """Test searching Notion content"""
    async with client as c:
        response = await c.call_tool(
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