from notion_client import Client
from typing import Optional

def get_notion_page_text(auth_token: str, page_id: str) -> Optional[str]:
    """
    Retrieves and extracts plain text content from a Notion page.

    Parameters:
        auth_token (str): Notion integration token.
        page_id (str): The ID of the Notion page.

    Returns:
        str or None: Extracted text content from the page, or None on failure.
    """
    try:
        # Initialize the Notion client
        notion = Client(auth=auth_token)

        # Get all block children (i.e., content inside the page)
        response = notion.blocks.children.list(block_id=page_id)

        def extract_text(block):
            block_type = block.get("type")
            if block_type and block_type in block:
                rich_text = block[block_type].get("rich_text", [])
                return ''.join(t.get("plain_text", "") for t in rich_text)
            return ""

        # Extract and join all block texts
        content = "\n".join(extract_text(block) for block in response.get("results", []))
        return content if content else None

    except Exception as e:
        print(f"Error retrieving Notion page content: {e}")
        return None