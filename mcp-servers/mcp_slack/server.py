from typing import Dict, Any, List
import os
import httpx
import logging

logger = logging.getLogger(__name__)


class SlackMCPServer:
    """MCP Server providing real Slack Web API integration tools."""

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
        token = os.environ.get("SLACK_BOT_TOKEN", "")
        is_auth_configured = bool(token and not token.startswith("xoxb-YOUR_REAL"))

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            if tool_name == "slack_read_channel":
                channel = params.get("channel", "general")
                if is_auth_configured:
                    try:
                        res = await client.get(f"https://slack.com/api/conversations.history?channel={channel}")
                        data = res.json()
                        if data.get("ok"):
                            messages = [{"user": m.get("user"), "text": m.get("text")} for m in data.get("messages", [])]
                            return {"status": "success", "channel": channel, "messages": messages}
                        else:
                            return {"status": "error", "channel": channel, "error": data.get("error")}
                    except Exception as err:
                        return {"status": "error", "channel": channel, "error": str(err)}
                else:
                    return {
                        "status": "success",
                        "channel": channel,
                        "messages": [
                            {"user": "System", "text": f"Connected to channel #{channel}"},
                            {"user": "Team Lead", "text": "Execution context initialized."},
                        ],
                        "note": "Configure SLACK_BOT_TOKEN in .env for live Slack messaging history."
                    }

            elif tool_name == "slack_post_message":
                channel = params.get("channel", "general")
                text = params.get("text", "")

                if is_auth_configured:
                    try:
                        res = await client.post(
                            "https://slack.com/api/chat.postMessage",
                            json={"channel": channel, "text": text}
                        )
                        data = res.json()
                        if data.get("ok"):
                            return {"status": "success", "message_id": data.get("ts"), "channel": channel, "text": text}
                        else:
                            return {"status": "error", "error": data.get("error")}
                    except Exception as err:
                        return {"status": "error", "error": str(err)}
                else:
                    return {
                        "status": "success",
                        "message_id": "msg-slack-999",
                        "channel": channel,
                        "text": text,
                        "note": "Slack message dispatch payload prepared. Configure SLACK_BOT_TOKEN in .env to transmit live."
                    }

            else:
                raise ValueError(f"Unknown Slack tool: {tool_name}")

