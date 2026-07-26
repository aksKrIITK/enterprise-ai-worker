import React, { useState } from 'react';
import { UserContext, AuditLog } from '../types';
import { Activity, ShieldCheck, Filter, Hash } from 'lucide-react';

interface AuditLogViewerProps {
  userContext: UserContext;
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ userContext }) => {
  const [logs] = useState<AuditLog[]>([
    {
      id: 'log-101',
      tenant_id: userContext.tenantId,
      actor_id: userContext.userId,
      action: 'CHAT_STREAM_STARTED',
      resource_type: 'CONVERSATION',
      resource_id: 'conv-100',
      trace_id: 'trace-8849-acme',
      timestamp: new Date(Date.now() - 60000).toLocaleTimeString(),
    },
    {
      id: 'log-102',
      tenant_id: userContext.tenantId,
      actor_id: userContext.userId,
      action: 'TOOL_CALL_EXECUTED',
      resource_type: 'MCP_TOOL',
      resource_id: 'gmail_send_email',
      trace_id: 'trace-8849-acme',
      timestamp: new Date(Date.now() - 30000).toLocaleTimeString(),
    },
    {
      id: 'log-103',
      tenant_id: userContext.tenantId,
      actor_id: 'admin-alice',
      action: 'APPROVAL_GRANTED',
      resource_type: 'APPROVAL_REQUEST',
      resource_id: 'req-440',
      trace_id: 'trace-8849-acme',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  return (
    <div className="flex-1 p-6 bg-dark-bg overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-dark-border pb-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <Activity className="w-6 h-6 text-emerald-400" />
              <span>SOC2 Audit Trail Viewer</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Immutable audit records for tenant <span className="text-white font-mono">{userContext.tenantId}</span> with distributed trace correlation headers.
            </p>
          </div>
        </div>

        {/* Table */}
        <div className="glass-panel rounded-2xl overflow-hidden border border-dark-border">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-sidebar text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-dark-border">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Resource</th>
                <th className="py-3 px-4">Actor ID</th>
                <th className="py-3 px-4">Trace ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border text-slate-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-dark-hover/50 transition-all">
                  <td className="py-3 px-4 text-slate-400 font-mono">{log.timestamp}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold text-[11px] border border-emerald-500/20">
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">{log.resource_type} / {log.resource_id}</td>
                  <td className="py-3 px-4 text-slate-300">{log.actor_id}</td>
                  <td className="py-3 px-4 text-cyan-400 font-mono flex items-center space-x-1">
                    <Hash className="w-3 h-3 shrink-0" />
                    <span>{log.trace_id}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
