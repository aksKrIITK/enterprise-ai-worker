export type Role = 'OWNER' | 'ADMIN' | 'MEMBER' | 'VIEWER';

export interface UserContext {
  userId: string;
  tenantId: string;
  email: string;
  role: Role;
  token: string;
}

export interface Citation {
  document_id: string;
  chunk_id: string;
  source_type: string;
  title: string;
  snippet: string;
}


export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_source?: string;
  citations?: Citation[];
  timestamp: string;
}

export interface AgentStepTrace {
  agent: string;
  status: string;
  message: string;
  trace_id?: string;
  timestamp: string;
}

export interface ApprovalRequest {
  id: string;
  tenant_id: string;
  conversation_id: string;
  task_id: string;
  requested_action: string;
  payload: Record<string, any>;
  risk_level: 'low' | 'medium' | 'high';
  requested_by_agent: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  approver_id?: string;
  created_at: string;
}

export interface AuditLog {
  id: string;
  tenant_id: string;
  actor_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  trace_id?: string;
  timestamp: string;
  details?: Record<string, any>;
}
