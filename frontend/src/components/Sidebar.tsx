import React from 'react';
import { MessageSquare, ShieldAlert, FileText, Activity } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  pendingApprovalsCount,
}) => {
  const navItems = [
    { id: 'chat', label: 'Agent Console', icon: MessageSquare },
    { id: 'approvals', label: 'HITL Approvals', icon: ShieldAlert, badge: pendingApprovalsCount },
    { id: 'documents', label: 'Document Portal', icon: FileText },
    { id: 'audit', label: 'Audit Trail', icon: Activity },
  ];

  return (
    <aside className="w-64 border-r border-dark-border bg-dark-sidebar flex flex-col justify-between py-6 px-4 shrink-0">
      <div className="space-y-6">
        <div className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Navigation
        </div>
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-lg shadow-indigo-500/25'
                    : 'text-slate-400 hover:text-white hover:bg-dark-hover'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-rose-500 text-white font-bold animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Security Isolation Status Pill */}
      <div className="p-3.5 rounded-xl bg-dark-card border border-dark-border space-y-2">
        <div className="flex items-center space-x-2 text-xs font-medium text-slate-300">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Tenant Isolation Active</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          PostgreSQL RLS & pgvector security predicates enforced on all queries.
        </p>
      </div>
    </aside>
  );
};
