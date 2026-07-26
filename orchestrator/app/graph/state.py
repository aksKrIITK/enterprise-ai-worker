from typing import List, Dict, Any, Optional, Literal, TypedDict
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    source_type: str
    title: str
    snippet: str


class ToolCallLog(BaseModel):
    tool_name: str
    input_params: Dict[str, Any]
    output_result: Dict[str, Any]
    timestamp: str


class AgentInput(BaseModel):
    task_id: str
    tenant_id: str
    user_id: str
    user_role: str = "MEMBER"
    user_acls: List[str] = Field(default_factory=list)
    instruction: str
    context: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: str


class AgentOutput(BaseModel):
    task_id: str
    status: Literal["success", "needs_approval", "failed", "partial"]
    result: Dict[str, Any]
    citations: List[Citation] = Field(default_factory=list)
    approval_request: Optional[Dict[str, Any]] = None
    tokens_used: int = 0
    tool_calls: List[ToolCallLog] = Field(default_factory=list)


class SubTask(BaseModel):
    task_id: str
    agent_type: str  # "researcher", "document_agent", etc.
    instruction: str
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[Dict[str, Any]] = None


class TaskGraphState(TypedDict):
    conversation_id: str
    tenant_id: str
    user_id: str
    user_role: str
    user_acls: List[str]
    messages: List[Dict[str, Any]]
    subtasks: List[Dict[str, Any]]
    current_subtask_index: int
    citations: List[Dict[str, Any]]
    intermediate_steps: List[Dict[str, Any]]
    next_step: str
    final_response: Optional[str]
