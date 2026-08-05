from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.approval.approval import ApprovalManager, ApprovalRequestModel
from app.mcp.mcp_client import MCPClient

# Module logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])
approval_manager = ApprovalManager()
mcp_client = MCPClient()


class DecisionRequest(BaseModel):
    """Payload model for approving or rejecting human-in-the-loop requests."""
    approver_id: Optional[str] = "admin-user-1"
    rejection_reason: Optional[str] = None


@router.get("/pending", response_model=List[ApprovalRequestModel])
async def list_pending_approvals(x_tenant_id: Optional[str] = Header("default-tenant")):
    """
    Retrieves all pending human approval requests for the specified tenant.
    """
    logger.info("Fetching pending approval requests for tenant: %s", x_tenant_id)
    try:
        pending = approval_manager.get_pending_requests(x_tenant_id)
        logger.debug("Found %d pending requests for tenant %s", len(pending), x_tenant_id)
        return pending
    except Exception as err:
        logger.error("Failed to list pending approvals for tenant %s: %s", x_tenant_id, err, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve pending approvals.")


@router.post("/{request_id}/approve", response_model=ApprovalRequestModel)
async def approve_request(
    request_id: str,
    body: DecisionRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    """
    Approves a pending request and triggers execution of the associated MCP tool action.
    """
    logger.info("Processing approval for request_id=%s, tenant=%s, approver=%s", request_id, x_tenant_id, body.approver_id)
    
    req = approval_manager.get_request(request_id)
    if not req:
        logger.warning("Approval request %s not found.", request_id)
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if req.tenant_id != x_tenant_id:
        logger.warning("Tenant boundary violation for request %s (req tenant: %s, caller tenant: %s)", request_id, req.tenant_id, x_tenant_id)
        raise HTTPException(status_code=403, detail="Tenant boundary violation.")

    updated_req = approval_manager.approve_request(request_id, body.approver_id or "admin-1")

    # Execute approved action via MCP client with error handling
    tool_name = req.requested_action
    logger.info("Executing approved action '%s' for request %s", tool_name, request_id)
    try:
        await mcp_client.execute_tool(tool_name, req.payload)
        logger.info("Successfully executed action '%s' for approved request %s", tool_name, request_id)
    except Exception as err:
        logger.error("Error executing approved action '%s' for request %s: %s", tool_name, request_id, err, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Approval registered, but execution of action '{tool_name}' failed: {err}"
        )

    return updated_req


@router.post("/{request_id}/reject", response_model=ApprovalRequestModel)
async def reject_request(
    request_id: str,
    body: DecisionRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    """
    Rejects a pending action request with an optional reason.
    """
    logger.info("Processing rejection for request_id=%s, tenant=%s, approver=%s", request_id, x_tenant_id, body.approver_id)
    
    req = approval_manager.get_request(request_id)
    if not req:
        logger.warning("Rejection target request %s not found.", request_id)
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if req.tenant_id != x_tenant_id:
        logger.warning("Tenant boundary violation on rejection for request %s", request_id)
        raise HTTPException(status_code=403, detail="Tenant boundary violation.")

    reason = body.rejection_reason or "Action rejected by human reviewer."
    updated_req = approval_manager.reject_request(request_id, body.approver_id or "admin-1", reason)
    logger.info("Request %s successfully rejected.", request_id)

    return updated_req

