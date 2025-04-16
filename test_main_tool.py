"""
Test for the main test tool.
"""
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import SSETransport

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_main_tool():
    """Test the test_tool functionality"""
    try:
        async with Client(SSETransport("http://localhost:8050/mcp")) as client:
            response = await client.call_tool("test_tool", {})
            print("\nResponse:", response)
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_main_tool()) 