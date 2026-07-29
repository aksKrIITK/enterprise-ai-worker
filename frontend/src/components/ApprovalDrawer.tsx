import React, { useState, useEffect } from 'react';
import { UserContext, ApprovalRequest } from '../types';
import { apiService } from '../services/api';
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle, Clock, RefreshCw } from 'lucide-react';

interface ApprovalDrawerProps {
  userContext: UserContext;
  onApprovalDecision: () => void;
}

export const ApprovalDrawer: React.FC<ApprovalDrawerProps> = ({ userContext, onApprovalDecision }) => {
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [rejectionReason, setRejectionReason] = useState<{ [id: string]: string }>({});

  const fetchApprovals = async () => {
    setLoading(true);
    const pending = await apiService.getPendingApprovals(userContext.tenantId);
    setRequests(pending);
    setLoading(false);
  };

  useEffect(() => {
    fetchApprovals();
  }, [userContext.tenantId]);

  const handleApprove = async (id: string) => {
    await apiService.approveRequest(id, userContext.tenantId);
    fetchApprovals();
    onApprovalDecision();
  };

  const handleReject = async (id: string) => {
    const reason = rejectionReason[id] || 'Rejected by reviewer';
    await apiService.rejectRequest(id, userContext.tenantId, reason);
    fetchApprovals();
    onApprovalDecision();
  };

  return (
    <div className="flex-1 p-6 bg-slate-50 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <ShieldAlert className="w-6 h-6 text-rose-500" />
              <span>Human-in-the-Loop Approval Queue</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Review and authorize pending write and external-facing operations for {userContext.tenantId}
            </p>
          </div>
          <button
            onClick={fetchApprovals}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 hover:text-slate-900 flex items-center space-x-2 shadow-xs font-medium"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Requests Feed */}
        {requests.length === 0 ? (
          <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-3 shadow-xs">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
            <h3 className="text-base font-semibold text-slate-900">No Pending Approval Requests</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              All write operations (sending emails, opening PRs, DML SQL) are clear. Trigger a write request in the Agent Console to test human approval gating.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {requests.map((req) => (
              <div key={req.id} className="p-5 bg-white border border-slate-200 rounded-2xl space-y-4 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider ${
                        req.risk_level === 'high'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {req.risk_level} Risk
                    </span>
                    <span className="text-sm font-semibold text-slate-900 font-mono">{req.requested_action}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(req.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Payload Preview */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-semibold uppercase text-slate-500 mb-2">Payload Preview:</div>
                  <pre className="text-xs font-mono text-indigo-900 overflow-x-auto font-medium">
                    {JSON.stringify(req.payload, null, 2)}
                  </pre>
                </div>

                {/* Rejection input and Action Triggers */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
                  <input
                    type="text"
                    placeholder="Reason for rejection (optional)..."
                    value={rejectionReason[req.id] || ''}
                    onChange={(e) => setRejectionReason({ ...rejectionReason, [req.id]: e.target.value })}
                    className="flex-1 bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                  />
                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => handleReject(req.id)}
                      className="flex-1 sm:flex-none px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center justify-center space-x-1.5"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject</span>
                    </button>
                    <button
                      onClick={() => handleApprove(req.id)}
                      className="flex-1 sm:flex-none px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 shadow-md shadow-emerald-500/20"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve & Execute</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
