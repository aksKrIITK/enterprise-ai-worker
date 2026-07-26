import pytest
from app.mcp.mcp_client import MCPClient

mcp_client = MCPClient()


def test_mcp_tool_discovery():
    tools = mcp_client.list_all_tools()
    assert len(tools) >= 5

    tool_names = [t["name"] for t in tools]
    assert "slack_post_message" in tool_names
    assert "gmail_send_email" in tool_names
    assert "calendar_create_event" in tool_names


@pytest.mark.asyncio
async def test_mcp_slack_tool_execution():
    res = await mcp_client.execute_tool("slack_read_channel", {"channel": "general"})
    assert res["status"] == "success"
    assert len(res["messages"]) > 0


@pytest.mark.asyncio
async def test_mcp_gmail_tool_execution():
    res = await mcp_client.execute_tool("gmail_read_inbox", {"query": "meeting"})
    assert res["status"] == "success"
    assert len(res["emails"]) > 0
