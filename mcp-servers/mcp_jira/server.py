from typing import Dict, Any, List


class JiraMCPServer:
    """MCP Server providing Jira integration tools."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "jira_get_issue",
                "description": "Get details of a Jira ticket by key.",
                "requires_approval": False,
                "input_schema": {"issue_key": "str"},
            },
            {
                "name": "jira_create_issue",
                "description": "Create a new Jira issue ticket.",
                "requires_approval": False,
                "input_schema": {"project": "str", "summary": "str", "issue_type": "str"},
            },
            {
                "name": "jira_transition_issue",
                "description": "Transition a Jira issue status (e.g. In Progress, Done).",
                "requires_approval": True,
                "risk_level": "medium",
                "input_schema": {"issue_key": "str", "status": "str"},
            },
        ]

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "jira_get_issue":
            issue_key = params.get("issue_key", "JIRA-101")
            return {
                "status": "success",
                "issue_key": issue_key,
                "summary": "Fix payment gateway timeout error",
                "status_name": "In Progress",
                "assignee": "Alice",
            }
        elif tool_name == "jira_create_issue":
            return {
                "status": "success",
                "issue_key": "JIRA-202",
                "summary": params.get("summary"),
                "project": params.get("project", "PROJ"),
            }
        elif tool_name == "jira_transition_issue":
            return {
                "status": "success",
                "issue_key": params.get("issue_key"),
                "new_status": params.get("status"),
            }
        else:
            raise ValueError(f"Unknown Jira tool: {tool_name}")
