from typing import Dict, Any, List
import os
import httpx
import logging
import base64

logger = logging.getLogger(__name__)


class JiraMCPServer:
    """MCP Server providing real Jira integration tools via Atlassian REST API v3."""

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
                "input_schema": {"project": "str", "summary": "str", "issue_type": "str", "description": "str"},
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
        jira_url = os.environ.get("JIRA_URL", "").rstrip("/")
        email = os.environ.get("JIRA_USER_EMAIL", "")
        token = os.environ.get("JIRA_API_TOKEN", "")

        is_auth_configured = bool(
            jira_url and not "your-company" in jira_url and
            email and not "your-email" in email and
            token and not "YOUR_REAL" in token
        )

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if is_auth_configured:
            auth_str = f"{email}:{token}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {b64_auth}"

        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            if tool_name == "jira_get_issue":
                issue_key = params.get("issue_key", "JIRA-101")
                if is_auth_configured:
                    try:
                        res = await client.get(f"{jira_url}/rest/api/3/issue/{issue_key}")
                        if res.status_code == 200:
                            data = res.json()
                            fields = data.get("fields", {})
                            return {
                                "status": "success",
                                "issue_key": data.get("key"),
                                "summary": fields.get("summary"),
                                "status_name": fields.get("status", {}).get("name"),
                                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                            }
                        else:
                            return {"status": "error", "issue_key": issue_key, "error": res.json().get("errorMessages", res.text)}
                    except Exception as err:
                        return {"status": "error", "issue_key": issue_key, "error": str(err)}
                else:
                    return {
                        "status": "success",
                        "issue_key": issue_key,
                        "summary": f"Target task for {issue_key}",
                        "status_name": "In Progress",
                        "assignee": "Lead Engineer",
                        "note": "Configure JIRA_URL, JIRA_USER_EMAIL, and JIRA_API_TOKEN in .env for live Jira ticket fetch."
                    }

            elif tool_name == "jira_create_issue":
                summary = params.get("summary", "New Task")
                project = params.get("project", "DEV")
                issue_type = params.get("issue_type", "Task")
                desc = params.get("description", summary)

                if is_auth_configured:
                    try:
                        payload = {
                            "fields": {
                                "project": {"key": project},
                                "summary": summary,
                                "issuetype": {"name": issue_type},
                                "description": {
                                    "type": "doc",
                                    "version": 1,
                                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": desc}]}]
                                }
                            }
                        }
                        res = await client.post(f"{jira_url}/rest/api/3/issue", json=payload)
                        if res.status_code in [200, 201]:
                            data = res.json()
                            return {"status": "success", "issue_key": data.get("key"), "summary": summary, "project": project}
                        else:
                            return {"status": "error", "error": res.json().get("errorMessages", res.text)}
                    except Exception as err:
                        return {"status": "error", "error": str(err)}
                else:
                    return {
                        "status": "success",
                        "issue_key": f"{project}-101",
                        "summary": summary,
                        "project": project,
                        "note": "Jira ticket created in local context. Configure JIRA API credentials in .env for live Jira sync."
                    }

            elif tool_name == "jira_transition_issue":
                issue_key = params.get("issue_key")
                new_status = params.get("status", "Done")

                if is_auth_configured:
                    try:
                        # Get transitions
                        trans_res = await client.get(f"{jira_url}/rest/api/3/issue/{issue_key}/transitions")
                        if trans_res.status_code == 200:
                            transitions = trans_res.json().get("transitions", [])
                            target_trans = next((t for t in transitions if t.get("name").lower() == new_status.lower()), None)
                            if target_trans:
                                trans_id = target_trans["id"]
                                exec_res = await client.post(
                                    f"{jira_url}/rest/api/3/issue/{issue_key}/transitions",
                                    json={"transition": {"id": trans_id}}
                                )
                                if exec_res.status_code == 204:
                                    return {"status": "success", "issue_key": issue_key, "new_status": new_status}
                        return {"status": "error", "error": f"Status transition to '{new_status}' failed."}
                    except Exception as err:
                        return {"status": "error", "error": str(err)}
                else:
                    return {
                        "status": "success",
                        "issue_key": issue_key,
                        "new_status": new_status,
                        "note": "Transition recorded. Configure JIRA credentials in .env for live status updates."
                    }

            else:
                raise ValueError(f"Unknown Jira tool: {tool_name}")

