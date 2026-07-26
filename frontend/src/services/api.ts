import axios from 'axios';
import { UserContext, ApprovalRequest, AuditLog } from '../types';

const GATEWAY_URL = 'http://localhost:8080';
const ORCHESTRATOR_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: GATEWAY_URL,
});

export const apiService = {
  // Generate dev token for testing
  async getDevToken(tenantId: string, role: string): Promise<UserContext> {
    try {
      const res = await client.post('/api/v1/auth/dev-token', {
        tenantId,
        role,
        email: `user@${tenantId}.com`,
      });
      return {
        userId: res.data.user_id,
        tenantId: res.data.tenant_id,
        email: res.data.email,
        role: res.data.role,
        token: res.data.token,
      };
    } catch {
      // Mock token for standalone frontend execution
      return {
        userId: 'u-101',
        tenantId,
        email: `dev@${tenantId}.com`,
        role: role as any,
        token: 'mock-jwt-token-12345',
      };
    }
  },

  // Stream chat responses with real-time SSE event callback
  streamChat(
    userContext: UserContext,
    conversationId: string,
    message: string,
    onStatusEvent: (event: any) => void,
    onTokenEvent: (delta: string) => void,
    onApprovalEvent: (approval: any) => void,
    onCompleteEvent: (result: any) => void,
  ) {
    const payload = {
      conversation_id: conversationId,
      messages: [{ role: 'user', content: message }],
    };

    fetch(`${ORCHESTRATOR_URL}/api/v1/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': userContext.tenantId,
        'X-User-Id': userContext.userId,
        'X-User-Role': userContext.role,
        'Authorization': `Bearer ${userContext.token}`,
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        if (!response.body) return;
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        const read = () => {
          reader.read().then(({ done, value }) => {
            if (done) return;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                const eventMatch = line.match(/^event:\s*(.+)\ndata:\s*(.+)$/s);
                if (eventMatch) {
                  const eventType = eventMatch[1].trim();
                  const eventData = JSON.parse(eventMatch[2].trim());

                  if (eventType === 'status') {
                    onStatusEvent(eventData);
                  } else if (eventType === 'token') {
                    onTokenEvent(eventData.delta);
                  } else if (eventType === 'needs_approval') {
                    onApprovalEvent(eventData);
                  } else if (eventType === 'result') {
                    onCompleteEvent(eventData);
                  }
                }
              }
            }
            read();
          });
        };
        read();
      })
      .catch((err) => console.error('SSE Stream Error:', err));
  },

  // Approvals API
  async getPendingApprovals(tenantId: string): Promise<ApprovalRequest[]> {
    try {
      const res = await axios.get(`${ORCHESTRATOR_URL}/api/v1/approvals/pending`, {
        headers: { 'X-Tenant-Id': tenantId },
      });
      return res.data;
    } catch {
      return [];
    }
  },

  async approveRequest(requestId: string, tenantId: string): Promise<any> {
    const res = await axios.post(`${ORCHESTRATOR_URL}/api/v1/approvals/${requestId}/approve`, {}, {
      headers: { 'X-Tenant-Id': tenantId },
    });
    return res.data;
  },

  async rejectRequest(requestId: string, tenantId: string, reason: string): Promise<any> {
    const res = await axios.post(`${ORCHESTRATOR_URL}/api/v1/approvals/${requestId}/reject`, { rejection_reason: reason }, {
      headers: { 'X-Tenant-Id': tenantId },
    });
    return res.data;
  },

  // Document Ingestion
  async ingestDocument(tenantId: string, title: string, content: string, acl: string[]): Promise<any> {

    const res = await axios.post(`${ORCHESTRATOR_URL}/api/v1/documents/ingest`, {
      title,
      content,
      acl,
    }, {
      headers: { 'X-Tenant-Id': tenantId },
    });
    return res.data;
  },

  async searchDocuments(tenantId: string, query: string): Promise<any> {
    const res = await axios.post(`${ORCHESTRATOR_URL}/api/v1/documents/search`, {
      query,
    }, {
      headers: { 'X-Tenant-Id': tenantId },
    });
    return res.data;
  },
};
