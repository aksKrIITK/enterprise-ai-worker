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
    <div className="h-screen w-screen flex flex-col bg-dark-bg text-slate-100 overflow-hidden font-sans">
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
