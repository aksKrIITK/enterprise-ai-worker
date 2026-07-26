from typing import Dict, Any, List, Optional
import sys
import os

# Add mcp-servers and root workspace directory to sys.path
mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../mcp-servers"))
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

from mcp_slack.server import SlackMCPServer
from mcp_gmail.server import GmailMCPServer
from mcp_calendar.server import CalendarMCPServer
from mcp_sql.server import SQLMCPServer
from mcp_jira.server import JiraMCPServer
from mcp_github.server import GitHubMCPServer


class MCPClient:
    """MCP Client registry for tool discovery and execution dispatch."""

    def __init__(self):
        self.servers = {
            "slack": SlackMCPServer(),
            "gmail": GmailMCPServer(),
            "calendar": CalendarMCPServer(),
            "sql": SQLMCPServer(),
            "jira": JiraMCPServer(),
            "github": GitHubMCPServer(),
        }

    def list_all_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for server in self.servers.values():
            tools.extend(server.get_tools())
        return tools

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        for tool in self.list_all_tools():
            if tool["name"] == tool_name:
                return tool
        return None

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name.startswith("slack_"):
            return await SlackMCPServer.execute_tool(tool_name, params)
        elif tool_name.startswith("gmail_"):
            return await GmailMCPServer.execute_tool(tool_name, params)
        elif tool_name.startswith("calendar_"):
            return await CalendarMCPServer.execute_tool(tool_name, params)
        elif tool_name.startswith("sql_"):
            return await SQLMCPServer.execute_tool(tool_name, params)
        elif tool_name.startswith("jira_"):
            return await JiraMCPServer.execute_tool(tool_name, params)
        elif tool_name.startswith("github_"):
            return await GitHubMCPServer.execute_tool(tool_name, params)
        else:
            raise ValueError(f"No registered MCP server for tool: {tool_name}")


