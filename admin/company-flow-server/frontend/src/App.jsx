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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
          {activeTab === 'persona' && <GeneratePersona onKickoff={() => setActiveTab('history')} />}
          {activeTab === 'crew' && <CrewProcess onNavigateHistory={() => setActiveTab('history')} />}
          {activeTab === 'history' && <ExecutionHistory />}
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
