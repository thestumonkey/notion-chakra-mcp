import os   
import json
import asyncio
from dotenv import load_dotenv
from src.common_utils import extract_response, get_mcp_client

# Load environment variables
load_dotenv()



async def test_setup_tools_record_dbs():
    """Test listing all accessible Notion databases"""
    async with get_mcp_client() as client:
        # tools = await client.list_tools()
        # print(tools)
        response = await client.call_tool("setup_record_dbs", {})
        response = extract_response(response)
        print(json.dumps(response, indent=4))
       
async def schema_tools_fetch_schemas():
    """Test listing all accessible Notion databases"""
    async with get_mcp_client() as client:
        # tools = await client.list_tools()
        # print(tools)
        response = await client.call_tool("schema_fetch_schemas", {})
        response = extract_response(response)
        print(json.dumps(response, indent=4))
       


if __name__ == "__main__":
    asyncio.run(schema_tools_fetch_schemas())
