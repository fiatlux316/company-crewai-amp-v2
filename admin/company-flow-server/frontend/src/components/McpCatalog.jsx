
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

export default function McpCatalog() {
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);

  useEffect(() => {
    api.fetchMcpTools().then(d => setTools(d.tools)).catch(console.error);
  }, []);

  return (
    <section id="mcp" className="view active">
      <div className="simple">
        <aside>
          <h2>MCP Tools</h2>
          <div id="mcpList">
            {tools.map((t, i) => (
              <div key={i} className="card" onClick={() => setSelectedTool(t)}>
                <b>{t.name}</b>
                <div className="meta">{t.description}</div>
              </div>
            ))}
          </div>
        </aside>
        <main>
          {!selectedTool ? (
            <div className="empty">MCP Tool을 선택하면 Input / Output Schema를 표시합니다.</div>
          ) : (
            <div>
              <h2>{selectedTool.name}</h2>
              <p>{selectedTool.description}</p>
              <h3>Input Schema</h3>
              <pre className="schema">{JSON.stringify(selectedTool.inputSchema, null, 2)}</pre>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
