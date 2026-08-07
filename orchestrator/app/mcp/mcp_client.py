from typing import Dict, Any, List, Optional
import sys
import os
import logging

# Set up module logger
logger = logging.getLogger(__name__)

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
    """
    Model Context Protocol (MCP) Client Registry.
    
    Manages discovery, schema aggregation, and dispatching execution 
    requests across registered MCP tools (Slack, Gmail, Calendar, SQL, Jira, GitHub).
    """

    def __init__(self):
        """Initialize MCP servers registry."""
        try:
            self.servers = {
                "slack": SlackMCPServer(),
                "gmail": GmailMCPServer(),
                "calendar": CalendarMCPServer(),
                "sql": SQLMCPServer(),
                "jira": JiraMCPServer(),
                "github": GitHubMCPServer(),
            }
            logger.info("Successfully initialized MCPClient with %d registered servers.", len(self.servers))
        except Exception as err:
            logger.error("Failed to initialize MCPClient servers: %s", err, exc_info=True)
            raise RuntimeError(f"MCPClient initialization failed: {err}") from err

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        Aggregates available tools from all registered MCP server instances.
        
        Returns:
            List[Dict[str, Any]]: List of tool metadata schemas.
        """
        tools = []
        for server_name, server in self.servers.items():
            try:
                server_tools = server.get_tools()
                tools.extend(server_tools)
                logger.debug("Fetched %d tools from MCP server '%s'.", len(server_tools), server_name)
            except Exception as err:
                logger.error("Error retrieving tools from MCP server '%s': %s", server_name, err, exc_info=True)
        return tools

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Finds tool metadata schema by name across all registered servers.
        
        Args:
            tool_name (str): Name of the tool to look up.
            
        Returns:
            Optional[Dict[str, Any]]: Matching tool schema dictionary or None if missing.
        """
        if not tool_name:
            logger.warning("get_tool called with empty tool_name.")
            return None
            
        for tool in self.list_all_tools():
            if tool.get("name") == tool_name:
                return tool
                
        logger.warning("Tool '%s' not found in registered MCP tools.", tool_name)
        return None

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a target MCP tool by routing parameters to the appropriate tool server.
        
        Args:
            tool_name (str): The specific tool identifier (e.g. 'slack_send_message').
            params (Dict[str, Any]): Execution payload parameters.
            
        Returns:
            Dict[str, Any]: Tool execution result.
            
        Raises:
            ValueError: If no server matches the tool_name prefix.
            RuntimeError: If an error occurs during tool execution.
        """
        logger.info("Executing MCP tool '%s' with parameters: %s", tool_name, params)
        
        try:
            if tool_name.startswith("slack_"):
                res = await SlackMCPServer.execute_tool(tool_name, params)
            elif tool_name.startswith("gmail_"):
                res = await GmailMCPServer.execute_tool(tool_name, params)
            elif tool_name.startswith("calendar_"):
                res = await CalendarMCPServer.execute_tool(tool_name, params)
            elif tool_name.startswith("sql_"):
                res = await SQLMCPServer.execute_tool(tool_name, params)
            elif tool_name.startswith("jira_"):
                res = await JiraMCPServer.execute_tool(tool_name, params)
            elif tool_name.startswith("github_"):
                res = await GitHubMCPServer.execute_tool(tool_name, params)
            else:
                logger.error("Unsupported or unknown MCP tool prefix for '%s'.", tool_name)
                raise ValueError(f"No registered MCP server for tool: {tool_name}")
                
            logger.info("Successfully executed MCP tool '%s'.", tool_name)
            return res
        except ValueError:
            raise
        except Exception as err:
            logger.error("Failed to execute MCP tool '%s': %s", tool_name, err, exc_info=True)
            raise RuntimeError(f"Execution error in tool '{tool_name}': {err}") from err



