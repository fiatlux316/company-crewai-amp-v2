import React from 'react';

const TAB_TITLES = {
  persona: '👤 Generate Persona',
  crew: '⚙️ Crew Management',
  history: '📋 Execution History',
  flow: '🔀 Node Flow Designer',
  mcp: '🛠 MCP Tools Catalog',
  swagger: '📖 Swagger API Specification'
};

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="top-header">
      <div className="header-left">
        <span className="current-view-title">{TAB_TITLES[activeTab] || 'Agent Platform'}</span>
        <span className="environment-badge">v2.0 Enterprise</span>
      </div>
      <div className="header-right">
        <div className="system-status">
          <span className="status-dot online"></span>
          <span className="status-text">Engine Online</span>
        </div>
        <div className="header-divider"></div>
        <div className="quick-links">
          <button className={`header-link ${activeTab === 'swagger' ? 'active' : ''}`} onClick={() => setActiveTab('swagger')}>
            📖 API Docs
          </button>
          <button className={`header-link ${activeTab === 'mcp' ? 'active' : ''}`} onClick={() => setActiveTab('mcp')}>
            🛠 MCP Catalog
          </button>
        </div>
        <div className="header-divider"></div>
        <div className="workspace-tag">
          🚀 Company Private AMP
        </div>
      </div>
    </header>
  );
}
