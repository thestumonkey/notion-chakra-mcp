"""
Block creation and manipulation tools for Notion integration.
"""
from typing import Any, Dict, List, Optional
import logging
from fastmcp import FastMCP, Context


# Configure logging
logger = logging.getLogger(__name__)

# Create Block MCP server
block_mcp = FastMCP("blocks", description="Block manipulation tools")

def get_notion_client(ctx: Context):
    """Get the Notion client from server state"""
    return ctx.request_context.lifespan_context.notion_client

class BlockBuilder:
    """Helper class to create block structures for Notion API"""
    
    @staticmethod
    def text(content: str, annotations: Optional[Dict[str, bool]] = None, link: Optional[str] = None) -> Dict[str, Any]:
        """Create a rich text object"""
        text = {"content": content, "link": {"url": link} if link else None}
        rich_text = {"type": "text", "text": text}
        if annotations:
            rich_text["annotations"] = annotations
        return rich_text

    @staticmethod
    def paragraph(content: str, annotations: Optional[Dict[str, bool]] = None, link: Optional[str] = None) -> Dict[str, Any]:
        """Create a paragraph block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [BlockBuilder.text(content, annotations, link)]
            }
        }

    @staticmethod
    def heading_1(content: str) -> Dict[str, Any]:
        """Create a heading 1 block"""
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [BlockBuilder.text(content)]
            }
        }

    @staticmethod
    def heading_2(content: str) -> Dict[str, Any]:
        """Create a heading 2 block"""
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [BlockBuilder.text(content)]
            }
        }

    @staticmethod
    def heading_3(content: str) -> Dict[str, Any]:
        """Create a heading 3 block"""
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [BlockBuilder.text(content)]
            }
        }

    @staticmethod
    def bulleted_list_item(content: str, annotations: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Create a bulleted list item block"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [BlockBuilder.text(content, annotations)]
            }
        }

    @staticmethod
    def numbered_list_item(content: str, annotations: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Create a numbered list item block"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [BlockBuilder.text(content, annotations)]
            }
        }

    @staticmethod
    def to_do(content: str, checked: bool = False) -> Dict[str, Any]:
        """Create a to-do block"""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [BlockBuilder.text(content)],
                "checked": checked
            }
        }

    @staticmethod
    def toggle(content: str, children: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a toggle block"""
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [BlockBuilder.text(content)]
            }
        }
        if children:
            block["toggle"]["children"] = children
        return block

    @staticmethod
    def code(content: str, language: str = "plain text") -> Dict[str, Any]:
        """Create a code block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [BlockBuilder.text(content)],
                "language": language
            }
        }

    @staticmethod
    def callout(content: str, icon_emoji: str = "💡") -> Dict[str, Any]:
        """Create a callout block"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [BlockBuilder.text(content)],
                "icon": {"type": "emoji", "emoji": icon_emoji}
            }
        }

@block_mcp.tool()
async def create_blocks(ctx: Context, block_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create blocks as children of an existing block"""
    try:
        client = get_notion_client(ctx)
        response = await client.blocks.children.append(
            block_id=block_id,
            children=blocks
        )
        logger.info(f"Created {len(blocks)} blocks under {block_id}")
        return response
    except Exception as e:
        logger.error(f"Error creating blocks for {block_id}: {e}")
        raise

@block_mcp.tool()
async def update_block(ctx: Context, block_id: str, block_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing block"""
    try:
        client = get_notion_client(ctx)
        response = await client.blocks.update(
            block_id=block_id,
            **block_data
        )
        logger.info(f"Updated block {block_id}")
        return response
    except Exception as e:
        logger.error(f"Error updating block {block_id}: {e}")
        raise

@block_mcp.tool()
async def delete_block(ctx: Context, block_id: str) -> Dict[str, Any]:
    """Delete a block"""
    try:
        client = get_notion_client(ctx)
        response = await client.blocks.delete(block_id=block_id)
        logger.info(f"Deleted block {block_id}")
        return response
    except Exception as e:
        logger.error(f"Error deleting block {block_id}: {e}")
        raise 