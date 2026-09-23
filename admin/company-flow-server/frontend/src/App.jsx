
import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
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
      <div className="main-content">
        {activeTab === 'persona' && <GeneratePersona onKickoff={() => setActiveTab('history')} />}
        {activeTab === 'crew' && <CrewProcess />}
        {activeTab === 'history' && <ExecutionHistory />}
        {activeTab === 'flow' && <NodeFlowDesigner />}
        {activeTab === 'mcp' && <McpCatalog />}
      </div>
    </div>
  );
}

export default App;
