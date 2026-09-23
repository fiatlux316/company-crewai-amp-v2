
import React from 'react';

export default function Sidebar({ activeTab, setActiveTab, collapsed, onToggle }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} id="appSidebar">
      <div className="sidebar-header">
        <button className="toggle-btn" onClick={onToggle}>☰</button>
        <div className="brand">Agent Platform</div>
      </div>
      <div className="tabs">
        <button className={activeTab === 'persona' ? 'active' : ''} onClick={() => setActiveTab('persona')}>
          👤 <span className="tab-text">Generate Persona</span>
        </button>
        <button className={activeTab === 'crew' ? 'active' : ''} onClick={() => setActiveTab('crew')}>
          ⚙️ <span className="tab-text">Crew Process</span>
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          📋 <span className="tab-text">Execution History</span>
        </button>
        <button className={activeTab === 'flow' ? 'active' : ''} onClick={() => setActiveTab('flow')}>
          🔀 <span className="tab-text">Node Flow Designer</span>
        </button>
        <button className={activeTab === 'mcp' ? 'active' : ''} onClick={() => setActiveTab('mcp')}>
          🛠 <span className="tab-text">MCP Catalog</span>
        </button>
        <button className={activeTab === 'swagger' ? 'active' : ''} onClick={() => setActiveTab('swagger')}>
          📖 <span className="tab-text">Swagger API</span>
        </button>
      </div>
    </aside>
  );
}
