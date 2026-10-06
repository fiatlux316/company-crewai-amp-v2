import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import GeneratePersona from './components/GeneratePersona';
import GenerateCrew from './components/GenerateCrew';
import CrewProcess from './components/CrewProcess';
import ExecutionHistory from './components/ExecutionHistory';
import NodeFlowDesigner from './components/NodeFlowDesigner';
import McpCatalog from './components/McpCatalog';
import DialogContainer from './components/Dialog';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('persona');
  const [initialRunId, setInitialRunId] = useState(null);
  const [initialCrewId, setInitialCrewId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleNavigateHistory = (runId) => {
    if (runId) {
      setInitialRunId(runId);
    }
    setActiveTab('history');
  };

  const handleNavigateCrew = (crewId) => {
    if (crewId) {
      setInitialCrewId(crewId);
    }
    setActiveTab('crew');
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
          {activeTab === 'generate_crew' && <GenerateCrew onNavigateCrew={handleNavigateCrew} />}
          {activeTab === 'crew' && <CrewProcess onNavigateHistory={handleNavigateHistory} initialCrewId={initialCrewId} />}
          {activeTab === 'history' && <ExecutionHistory initialRunId={initialRunId} onNavigateCrew={handleNavigateCrew} />}
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
      <DialogContainer />
    </div>
  );
}

export default App;
