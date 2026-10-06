
import React from 'react';

export default function Sidebar({ activeTab, setActiveTab, collapsed, onToggle }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} id="appSidebar">
      <div className="sidebar-header">
        <button className="toggle-btn" onClick={onToggle}>☰</button>
        <div className="brand">Agent Platform</div>
      </div>
      <div className="tabs">
        <button title={collapsed ? "Generate Persona" : ""} className={activeTab === 'persona' ? 'active' : ''} onClick={() => setActiveTab('persona')}>
          👤 <span className="tab-text">Generate Persona</span>
        </button>
        <button title={collapsed ? "Generate Crew" : ""} className={activeTab === 'generate_crew' ? 'active' : ''} onClick={() => setActiveTab('generate_crew')}>
          ✨ <span className="tab-text">Generate Crew</span>
        </button>
        <button title={collapsed ? "Crew Management" : ""} className={activeTab === 'crew' ? 'active' : ''} onClick={() => setActiveTab('crew')}>
          ⚙️ <span className="tab-text">Crew Management</span>
        </button>
        <button title={collapsed ? "Execution History" : ""} className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          📋 <span className="tab-text">Execution History</span>
        </button>
        <button title={collapsed ? "Flow Designer" : ""} className={activeTab === 'flow' ? 'active' : ''} onClick={() => setActiveTab('flow')}>
          🔀 <span className="tab-text">Flow Designer</span>
        </button>
        <button title={collapsed ? "MCP Tools" : ""} className={activeTab === 'mcp' ? 'active' : ''} onClick={() => setActiveTab('mcp')}>
          🛠 <span className="tab-text">MCP Tools</span>
        </button>
        <button title={collapsed ? "Swagger API" : ""} className={activeTab === 'swagger' ? 'active' : ''} onClick={() => setActiveTab('swagger')}>
          📖 <span className="tab-text">Swagger API</span>
        </button>
      </div>
    </aside>
  );
}
