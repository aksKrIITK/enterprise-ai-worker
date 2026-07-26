from typing import Dict, Any, List


class SlackMCPServer:
    """MCP Server providing Slack integration tools."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "slack_read_channel",
                "description": "Read message history from a Slack channel.",
                "requires_approval": False,
                "input_schema": {"channel": "str"},
            },
            {
                "name": "slack_post_message",
                "description": "Post a message to a public or private Slack channel.",
                "requires_approval": True,
                "risk_level": "medium",
                "input_schema": {"channel": "str", "text": "str"},
            },
        ]

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "slack_read_channel":
            channel = params.get("channel", "general")
            return {
                "status": "success",
                "messages": [
                    {"user": "Alice", "text": f"Discussing project roadmap in #{channel}"},
                    {"user": "Bob", "text": "Deployment scheduled for 3 PM"},
                ],
            }
        elif tool_name == "slack_post_message":
            channel = params.get("channel")
            text = params.get("text")
            return {
                "status": "success",
                "message_id": "msg-slack-999",
                "channel": channel,
                "text": text,
            }
        else:
            raise ValueError(f"Unknown Slack tool: {tool_name}")
