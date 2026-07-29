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
    <header className="h-16 border-b border-slate-200 bg-white/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-slate-900 flex items-center space-x-2">
            <span>Enterprise AI Worker</span>
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">
              v1.0 Production
            </span>
          </h1>
          <p className="text-xs text-slate-500">Multi-Agent Platform & Security Gateway</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* System Health Indicators */}
        <div className="hidden md:flex items-center space-x-3 px-3 py-1.5 rounded-lg bg-slate-100/80 border border-slate-200 text-xs text-slate-700 font-medium">
          <div className="flex items-center space-x-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Gateway (8080)</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center space-x-1.5">
            <div className="w-2 h-2 rounded-full bg-teal-600 animate-pulse" />
            <span>Orchestrator (8000)</span>
          </div>
        </div>

        {/* Tenant Switcher */}
        <div className="flex items-center space-x-2 bg-slate-100/80 border border-slate-200 rounded-lg px-3 py-1.5 text-xs">
          <Database className="w-3.5 h-3.5 text-teal-600" />
          <span className="text-slate-500">Tenant:</span>
          <select
            value={userContext.tenantId}
            onChange={(e) => setUserContext({ ...userContext, tenantId: e.target.value })}
            className="bg-transparent text-slate-900 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="tenant-acme" className="bg-white text-slate-800">Acme Corp (tenant-acme)</option>
            <option value="tenant-globex" className="bg-white text-slate-800">Globex Inc (tenant-globex)</option>
            <option value="tenant-stark" className="bg-white text-slate-800">Stark Tech (tenant-stark)</option>
          </select>
        </div>

        {/* User Role Switcher */}
        <div className="flex items-center space-x-2 bg-slate-100/80 border border-slate-200 rounded-lg px-3 py-1.5 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span className="text-slate-500">Role:</span>
          <select
            value={userContext.role}
            onChange={(e) => setUserContext({ ...userContext, role: e.target.value as any })}
            className="bg-transparent text-slate-900 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="ADMIN" className="bg-white text-slate-800">ADMIN</option>
            <option value="OWNER" className="bg-white text-slate-800">OWNER</option>
            <option value="MEMBER" className="bg-white text-slate-800">MEMBER</option>
            <option value="VIEWER" className="bg-white text-slate-800">VIEWER</option>
          </select>
        </div>
      </div>
    </header>
  );
};
