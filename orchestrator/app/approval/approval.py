import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel


class ApprovalRequestModel(BaseModel):
    id: str
    tenant_id: str
    conversation_id: str
    task_id: str
    requested_action: str
    payload: Dict[str, Any]
    risk_level: Literal["low", "medium", "high"] = "medium"
    requested_by_agent: str
    status: Literal["pending", "approved", "rejected", "expired"] = "pending"
    approver_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str
    decided_at: Optional[str] = None


class ApprovalManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApprovalManager, cls).__new__(cls)
            cls._instance.requests = {}
            cls._instance.checkpoints = {}
        return cls._instance

    def create_approval_request(
        self,
        tenant_id: str,
        conversation_id: str,
        task_id: str,
        requested_action: str,
        payload: Dict[str, Any],
        requested_by_agent: str,
        risk_level: str = "medium",
        paused_state: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequestModel:
        request_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        req = ApprovalRequestModel(
            id=request_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            task_id=task_id,
            requested_action=requested_action,
            payload=payload,
            risk_level=risk_level,
            requested_by_agent=requested_by_agent,
            status="pending",
            created_at=now_str,
        )

        self.requests[request_id] = req
        if paused_state:
            self.checkpoints[request_id] = paused_state

        return req

    def get_pending_requests(self, tenant_id: str) -> List[ApprovalRequestModel]:
        return [
            r for r in self.requests.values()
            if r.tenant_id == tenant_id and r.status == "pending"
        ]

    def get_request(self, request_id: str) -> Optional[ApprovalRequestModel]:
        return self.requests.get(request_id)

    def approve_request(self, request_id: str, approver_id: str) -> Optional[ApprovalRequestModel]:
        req = self.requests.get(request_id)
        if not req:
            return None
        req.status = "approved"
        req.approver_id = approver_id
        req.decided_at = datetime.now(timezone.utc).isoformat()
        return req

    def reject_request(self, request_id: str, approver_id: str, reason: str = "") -> Optional[ApprovalRequestModel]:
        req = self.requests.get(request_id)
        if not req:
            return None
        req.status = "rejected"
        req.approver_id = approver_id
        req.rejection_reason = reason
        req.decided_at = datetime.now(timezone.utc).isoformat()
        return req

    def clear(self):
        self.requests = {}
        self.checkpoints = {}
