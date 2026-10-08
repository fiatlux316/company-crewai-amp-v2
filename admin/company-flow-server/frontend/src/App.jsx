import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import GeneratePersona from './components/GeneratePersona';
import GenerateCrew from './components/GenerateCrew';
import CrewProcess from './components/CrewProcess';
import ExecutionHistory from './components/ExecutionHistory';
import NodeFlowDesigner from './components/NodeFlowDesigner';
import McpCatalog from './components/McpCatalog';
import UserManagement from './components/UserManagement';
import Auth from './components/Auth';
import RAGChatbot from './components/RAGChatbot';
import DialogContainer from './components/Dialog';
import './index.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('persona');
  const [initialRunId, setInitialRunId] = useState(null);
  const [initialCrewId, setInitialCrewId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('access_token')) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleNavigateHistory = (runId) => {
    if (runId) setInitialRunId(runId);
    setActiveTab('history');
  };

  const handleNavigateCrew = (crewId) => {
    if (crewId) setInitialCrewId(crewId);
    setActiveTab('crew');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user_name');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="app-layout">
        <Auth onLogin={() => setIsAuthenticated(true)} />
        <DialogContainer />
      </div>
    );
  }

  const userType = localStorage.getItem('user_type');
  const userId = localStorage.getItem('user_id');

  return (
    <div className="app-layout">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
        userType={userType}
      />
      <div className="main-wrapper">
        <Header activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} />
        <div className="main-content">
          {activeTab === 'persona' && <GeneratePersona onKickoff={handleNavigateHistory} />}
          {activeTab === 'generate_crew' && <GenerateCrew onNavigateCrew={handleNavigateCrew} />}
          {activeTab === 'crew' && <CrewProcess onNavigateHistory={handleNavigateHistory} initialCrewId={initialCrewId} userType={userType} userId={userId} />}
          {activeTab === 'history' && <ExecutionHistory initialRunId={initialRunId} onNavigateCrew={handleNavigateCrew} userType={userType} userId={userId} />}
          {activeTab === 'flow' && <NodeFlowDesigner />}
          {activeTab === 'mcp' && <McpCatalog />}
          {activeTab === 'users' && <UserManagement />}
          {activeTab === 'rag' && <RAGChatbot />}
          {activeTab === 'swagger' && (
            <iframe
              src="/docs"
              style={{ width: '100%', height: '100%', border: 'none' }}
              title="Swagger API"
            />
          )}
        </div>
      </div>
      <DialogContainer />
    </div>
  );
}

export default App;
