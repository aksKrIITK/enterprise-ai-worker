from typing import Dict, Any, List


class CalendarMCPServer:
    """MCP Server providing Google Calendar tools."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "calendar_read_events",
                "description": "Read availability and upcoming calendar events.",
                "requires_approval": False,
                "input_schema": {"time_min": "str", "time_max": "str"},
            },
            {
                "name": "calendar_create_event",
                "description": "Create a new meeting or calendar event.",
                "requires_approval": True,
                "risk_level": "medium",
                "input_schema": {"summary": "str", "start_time": "str", "attendees": "list"},
            },
        ]

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "calendar_read_events":
            return {
                "status": "success",
                "events": [
                    {"summary": "Team Sync", "start": "2026-07-27T10:00:00Z", "end": "2026-07-27T10:30:00Z"}
                ],
            }
        elif tool_name == "calendar_create_event":
            return {
                "status": "success",
                "event_id": "evt-777",
                "summary": params.get("summary"),
                "start_time": params.get("start_time"),
            }
        else:
            raise ValueError(f"Unknown Calendar tool: {tool_name}")
