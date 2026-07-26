import pytest
from app.mcp.mcp_client import MCPClient

mcp_client = MCPClient()


def test_dev_tools_discovery():
    tools = mcp_client.list_all_tools()
    tool_names = [t["name"] for t in tools]

    assert "jira_get_issue" in tool_names
    assert "jira_create_issue" in tool_names
    assert "github_read_repo" in tool_names
    assert "github_open_pr" in tool_names
    assert "github_merge_pr" in tool_names


@pytest.mark.asyncio
async def test_jira_tool_execution():
    res = await mcp_client.execute_tool("jira_get_issue", {"issue_key": "JIRA-999"})
    assert res["status"] == "success"
    assert res["issue_key"] == "JIRA-999"


@pytest.mark.asyncio
async def test_github_tool_execution():
    res = await mcp_client.execute_tool("github_read_repo", {"repo": "enterprise/ai-worker"})
    assert res["status"] == "success"
    assert "files" in res
