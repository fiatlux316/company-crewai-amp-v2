import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import GeneratePersona from './components/GeneratePersona';
import CrewProcess from './components/CrewProcess';
import ExecutionHistory from './components/ExecutionHistory';
import NodeFlowDesigner from './components/NodeFlowDesigner';
import McpCatalog from './components/McpCatalog';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('persona');
  const [initialRunId, setInitialRunId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleNavigateHistory = (runId) => {
    if (runId) {
      setInitialRunId(runId);
    }
    setActiveTab('history');
  };

  return (
    <div className="app-layout">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
      />
      <div className="main-wrapper">
        <Header activeTab={activeTab} setActiveTab={setActiveTab} />
        <div className="main-content">
          {activeTab === 'persona' && <GeneratePersona onKickoff={handleNavigateHistory} />}
          {activeTab === 'crew' && <CrewProcess onNavigateHistory={handleNavigateHistory} />}
          {activeTab === 'history' && <ExecutionHistory initialRunId={initialRunId} />}
          {activeTab === 'flow' && <NodeFlowDesigner />}
          {activeTab === 'mcp' && <McpCatalog />}
          {activeTab === 'swagger' && (
            <iframe
              src="/docs"
              style={{ width: '100%', height: '100%', border: 'none' }}
              title="Swagger API"
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
