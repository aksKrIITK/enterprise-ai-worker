import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class AuditLogRecord(BaseModel):
    id: str
    tenant_id: str
    actor_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    trace_id: str
    timestamp: str
    details: Dict[str, Any] = {}


class AuditLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuditLogger, cls).__new__(cls)
            cls._instance.records = []
        return cls._instance

    def log(
        self,
        tenant_id: str,
        actor_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        trace_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogRecord:
        record = AuditLogRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self.records.append(record)
        return record

    def get_tenant_audit_logs(self, tenant_id: str) -> List[AuditLogRecord]:
        return [r for r in self.records if r.tenant_id == tenant_id]

    def clear(self):
        self.records = []
