import React, { useState, useEffect } from 'react';
import { UserContext } from './types';
import { apiService } from './services/api';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatConsole } from './components/ChatConsole';
import { ApprovalDrawer } from './components/ApprovalDrawer';
import { DocumentPortal } from './components/DocumentPortal';
import { AuditLogViewer } from './components/AuditLogViewer';

export const App: React.FC = () => {
  const [userContext, setUserContext] = useState<UserContext>({
    userId: 'user-admin-1',
    tenantId: 'tenant-acme',
    email: 'admin@acme.com',
    role: 'ADMIN',
    token: 'mock-jwt-token-123',
  });

  const [activeTab, setActiveTab] = useState('chat');
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);

  const refreshPendingApprovals = async () => {
    const pending = await apiService.getPendingApprovals(userContext.tenantId);
    setPendingApprovalsCount(pending.length);
  };

  useEffect(() => {
    refreshPendingApprovals();
  }, [userContext.tenantId]);

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-50 text-slate-900 overflow-hidden font-sans relative">
      {/* Background Ambient Glow Accents */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />

      <Header
        userContext={userContext}
        setUserContext={setUserContext}
        pendingCount={pendingApprovalsCount}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pendingApprovalsCount={pendingApprovalsCount}
        />

        <main className="flex-1 flex overflow-hidden">
          {activeTab === 'chat' && (
            <ChatConsole
              userContext={userContext}
              onNewApprovalNeeded={refreshPendingApprovals}
            />
          )}

          {activeTab === 'approvals' && (
            <ApprovalDrawer
              userContext={userContext}
              onApprovalDecision={refreshPendingApprovals}
            />
          )}

          {activeTab === 'documents' && <DocumentPortal userContext={userContext} />}

          {activeTab === 'audit' && <AuditLogViewer userContext={userContext} />}
        </main>
      </div>
    </div>
  );
};

export default App;
