from typing import Dict, Any, List


class GmailMCPServer:
    """MCP Server providing Gmail integration tools."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "gmail_read_inbox",
                "description": "Search and read messages from Gmail inbox.",
                "requires_approval": False,
                "input_schema": {"query": "str"},
            },
            {
                "name": "gmail_draft_email",
                "description": "Create an email draft.",
                "requires_approval": False,
                "input_schema": {"to": "str", "subject": "str", "body": "str"},
            },
            {
                "name": "gmail_send_email",
                "description": "Send an email message via Gmail API.",
                "requires_approval": True,
                "risk_level": "high",
                "input_schema": {"to": "str", "subject": "str", "body": "str"},
            },
        ]

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "gmail_read_inbox":
            query = params.get("query", "")
            return {
                "status": "success",
                "emails": [
                    {"id": "em-101", "from": "client@acme.com", "subject": "Meeting confirmation", "snippet": "Can we confirm 2 PM?"}
                ],
            }
        elif tool_name == "gmail_draft_email":
            return {
                "status": "success",
                "draft_id": "draft-202",
                "to": params.get("to"),
                "subject": params.get("subject"),
                "body": params.get("body"),
            }
        elif tool_name == "gmail_send_email":
            return {
                "status": "success",
                "message_id": "sent-msg-303",
                "to": params.get("to"),
                "subject": params.get("subject"),
                "sent": True,
            }
        else:
            raise ValueError(f"Unknown Gmail tool: {tool_name}")
