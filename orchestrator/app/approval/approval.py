import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel

# Module logger
logger = logging.getLogger(__name__)


class ApprovalRequestModel(BaseModel):
    """Data model representing a human-in-the-loop approval request."""
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


import os
import json

class ApprovalManager:
    """
    Singleton Manager for human-in-the-loop approval requests and paused graph state checkpoints.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApprovalManager, cls).__new__(cls)
            cls._instance.requests = {}
            cls._instance.checkpoints = {}
            cls._instance.storage_file = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../approval_store_data.json")
            )
            cls._instance._load_from_storage()
            logger.info("Initialized ApprovalManager singleton instance.")
        return cls._instance

    def _load_from_storage(self):
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.requests = {k: ApprovalRequestModel(**v) for k, v in data.items()}
                logger.info("Loaded %d approval requests from persistent storage.", len(self.requests))
        except Exception as err:
            logger.error("Failed to load approval store: %s", err)

    def _save_to_storage(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.requests.items()}, f, indent=2)
            logger.debug("Saved %d approval requests to persistent storage.", len(self.requests))
        except Exception as err:
            logger.error("Failed to save approval store: %s", err)


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
        """
        Creates and registers a new approval request.
        """
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
        self._save_to_storage()

        logger.info(
            "Created approval request: id=%s, action='%s', tenant='%s', agent='%s', risk='%s'",
            request_id, requested_action, tenant_id, requested_by_agent, risk_level
        )
        return req

    def get_pending_requests(self, tenant_id: str) -> List[ApprovalRequestModel]:
        """
        Filters pending requests by tenant ID.
        """
        return [
            r for r in self.requests.values()
            if r.tenant_id == tenant_id and r.status == "pending"
        ]

    def get_request(self, request_id: str) -> Optional[ApprovalRequestModel]:
        """
        Retrieves request model by ID.
        """
        return self.requests.get(request_id)

    def approve_request(self, request_id: str, approver_id: str) -> Optional[ApprovalRequestModel]:
        """
        Marks an approval request as approved by the given approver ID.
        """
        req = self.requests.get(request_id)
        if not req:
            logger.warning("Attempted to approve non-existent request: id=%s", request_id)
            return None
        if req.status != "pending":
            logger.warning("Attempted to approve non-pending request id=%s (current status: %s)", request_id, req.status)
            
        req.status = "approved"
        req.approver_id = approver_id
        req.decided_at = datetime.now(timezone.utc).isoformat()
        self._save_to_storage()
        logger.info("Request id=%s marked as APPROVED by approver=%s", request_id, approver_id)
        return req

    def reject_request(self, request_id: str, approver_id: str, reason: str = "") -> Optional[ApprovalRequestModel]:
        """
        Marks an approval request as rejected by the given approver ID.
        """
        req = self.requests.get(request_id)
        if not req:
            logger.warning("Attempted to reject non-existent request: id=%s", request_id)
            return None
        if req.status != "pending":
            logger.warning("Attempted to reject non-pending request id=%s (current status: %s)", request_id, req.status)

        req.status = "rejected"
        req.approver_id = approver_id
        req.rejection_reason = reason
        req.decided_at = datetime.now(timezone.utc).isoformat()
        self._save_to_storage()
        logger.info("Request id=%s marked as REJECTED by approver=%s (reason: %s)", request_id, approver_id, reason)
        return req

    def clear(self):
        """Clears all stored requests and checkpoints."""
        self.requests = {}
        self.checkpoints = {}
        self._save_to_storage()
        logger.info("Cleared all approval requests and checkpoints from ApprovalManager.")


