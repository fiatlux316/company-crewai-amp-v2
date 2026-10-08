
import React from 'react';

export default function Sidebar({ activeTab, setActiveTab, collapsed, onToggle, userType }) {
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
        <button className={activeTab === 'generate_crew' ? 'active' : ''} onClick={() => setActiveTab('generate_crew')}>
          ✨ <span className="tab-text">Generate Crew</span>
        </button>
        <button className={activeTab === 'crew' ? 'active' : ''} onClick={() => setActiveTab('crew')}>
          ⚙️ <span className="tab-text">Crew Management</span>
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          📋 <span className="tab-text">Execution History</span>
        </button>
        <button className={activeTab === 'flow' ? 'active' : ''} onClick={() => setActiveTab('flow')}>
          🔀 <span className="tab-text">Flow Designer</span>
        </button>
        <button className={activeTab === 'mcp' ? 'active' : ''} onClick={() => setActiveTab('mcp')}>
          🛠 <span className="tab-text">MCP Tools</span>
        </button>
        <button className={activeTab === 'swagger' ? 'active' : ''} onClick={() => setActiveTab('swagger')}>
          📖 <span className="tab-text">Swagger API</span>
        </button>
        <button className={activeTab === 'rag' ? 'active' : ''} onClick={() => setActiveTab('rag')}>
          💬 <span className="tab-text">AI Chatbot</span>
        </button>
      </div>

      {userType === '1' && (
        <div className="tabs" style={{ marginTop: 'auto', borderTop: '1px solid #1f2937' }}>
          <button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>
            👥 <span className="tab-text">User Management</span>
          </button>
        </div>
      )}
    </aside>
  );
}
