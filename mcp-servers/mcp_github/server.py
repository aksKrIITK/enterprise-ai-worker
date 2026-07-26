from typing import Dict, Any, List


class GitHubMCPServer:
    """MCP Server providing GitHub integration tools."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "github_read_repo",
                "description": "Read files and repository metadata.",
                "requires_approval": False,
                "input_schema": {"repo": "str", "path": "str"},
            },
            {
                "name": "github_create_branch",
                "description": "Create a new git branch.",
                "requires_approval": False,
                "input_schema": {"repo": "str", "branch_name": "str"},
            },
            {
                "name": "github_open_pr",
                "description": "Open a Pull Request on a GitHub repository.",
                "requires_approval": True,
                "risk_level": "high",
                "input_schema": {"repo": "str", "title": "str", "head": "str", "base": "str"},
            },
            {
                "name": "github_merge_pr",
                "description": "Merge an open Pull Request on GitHub.",
                "requires_approval": True,
                "risk_level": "high",
                "input_schema": {"repo": "str", "pr_number": "int"},
            },
        ]

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "github_read_repo":
            repo = params.get("repo", "enterprise/app")
            return {
                "status": "success",
                "repo": repo,
                "files": ["src/main.py", "pyproject.toml", "README.md"],
            }
        elif tool_name == "github_create_branch":
            return {
                "status": "success",
                "branch_name": params.get("branch_name"),
                "ref": f"refs/heads/{params.get('branch_name')}",
            }
        elif tool_name == "github_open_pr":
            return {
                "status": "success",
                "pr_number": 42,
                "pr_url": f"https://github.com/{params.get('repo')}/pull/42",
                "title": params.get("title"),
            }
        elif tool_name == "github_merge_pr":
            return {
                "status": "success",
                "pr_number": params.get("pr_number"),
                "merged": True,
            }
        else:
            raise ValueError(f"Unknown GitHub tool: {tool_name}")
