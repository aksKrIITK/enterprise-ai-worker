import React from 'react';
import { UserContext } from '../types';
import { ShieldCheck, Cpu, Database, User } from 'lucide-react';

interface HeaderProps {
  userContext: UserContext;
  setUserContext: React.Dispatch<React.SetStateAction<UserContext>>;
  pendingCount: number;
}

export const Header: React.FC<HeaderProps> = ({ userContext, setUserContext, pendingCount }) => {
  return (
    <header className="h-16 border-b border-dark-border bg-dark-sidebar/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center space-x-2">
            <span>Enterprise AI Worker</span>
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
              v1.0 Production
            </span>
          </h1>
          <p className="text-xs text-slate-400">Multi-Agent Platform & Security Gateway</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* System Health Indicators */}
        <div className="hidden md:flex items-center space-x-3 px-3 py-1.5 rounded-lg bg-dark-bg border border-dark-border text-xs text-slate-300">
          <div className="flex items-center space-x-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Gateway (8080)</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1.5">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Orchestrator (8000)</span>
          </div>
        </div>

        {/* Tenant Switcher */}
        <div className="flex items-center space-x-2 bg-dark-bg border border-dark-border rounded-lg px-3 py-1.5 text-xs">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Tenant:</span>
          <select
            value={userContext.tenantId}
            onChange={(e) => setUserContext({ ...userContext, tenantId: e.target.value })}
            className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
          >
            <option value="tenant-acme" className="bg-dark-card text-white">Acme Corp (tenant-acme)</option>
            <option value="tenant-globex" className="bg-dark-card text-white">Globex Inc (tenant-globex)</option>
            <option value="tenant-stark" className="bg-dark-card text-white">Stark Tech (tenant-stark)</option>
          </select>
        </div>

        {/* User Role Switcher */}
        <div className="flex items-center space-x-2 bg-dark-bg border border-dark-border rounded-lg px-3 py-1.5 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-400">Role:</span>
          <select
            value={userContext.role}
            onChange={(e) => setUserContext({ ...userContext, role: e.target.value as any })}
            className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
          >
            <option value="ADMIN" className="bg-dark-card text-white">ADMIN</option>
            <option value="OWNER" className="bg-dark-card text-white">OWNER</option>
            <option value="MEMBER" className="bg-dark-card text-white">MEMBER</option>
            <option value="VIEWER" className="bg-dark-card text-white">VIEWER</option>
          </select>
        </div>
      </div>
    </header>
  );
};
