from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.approval.approval import ApprovalManager, ApprovalRequestModel
from app.mcp.mcp_client import MCPClient

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])
approval_manager = ApprovalManager()
mcp_client = MCPClient()


class DecisionRequest(BaseModel):
    approver_id: Optional[str] = "admin-user-1"
    rejection_reason: Optional[str] = None


@router.get("/pending", response_model=List[ApprovalRequestModel])
async def list_pending_approvals(x_tenant_id: Optional[str] = Header("default-tenant")):
    return approval_manager.get_pending_requests(x_tenant_id)


@router.post("/{request_id}/approve", response_model=ApprovalRequestModel)
async def approve_request(
    request_id: str,
    body: DecisionRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    req = approval_manager.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if req.tenant_id != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant boundary violation.")

    updated_req = approval_manager.approve_request(request_id, body.approver_id or "admin-1")

    # Execute approved action via MCP client
    tool_name = req.requested_action
    await mcp_client.execute_tool(tool_name, req.payload)

    return updated_req


@router.post("/{request_id}/reject", response_model=ApprovalRequestModel)
async def reject_request(
    request_id: str,
    body: DecisionRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    req = approval_manager.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if req.tenant_id != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant boundary violation.")

    reason = body.rejection_reason or "Action rejected by human reviewer."
    updated_req = approval_manager.reject_request(request_id, body.approver_id or "admin-1", reason)

    return updated_req
