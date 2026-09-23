import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

function SchemaTable({ schema }) {
  if (!schema || typeof schema !== 'object') {
    return <div className="hint">정의된 스키마가 없습니다.</div>;
  }

  const props = schema.properties || {};
  const requiredList = Array.isArray(schema.required) ? schema.required : [];
  const propKeys = Object.keys(props);

  if (propKeys.length === 0) {
    return (
      <div>
        <div className="hint" style={{ marginBottom: '8px' }}>Properties 항목이 비어있습니다.</div>
        <pre className="schema">{JSON.stringify(schema, null, 2)}</pre>
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="schema-table">
        <thead>
          <tr>
            <th>Property</th>
            <th>Type</th>
            <th>Required / Optional</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {propKeys.map(key => {
            const prop = props[key] || {};
            const isRequired = requiredList.includes(key);
            const typeStr = prop.type ? (Array.isArray(prop.type) ? prop.type.join(' | ') : prop.type) : 'any';

            return (
              <tr key={key}>
                <td>
                  <code className="prop-name">{key}</code>
                </td>
                <td>
                  <span className="prop-type">{typeStr}</span>
                </td>
                <td>
                  {isRequired ? (
                    <span className="schema-badge required">Required</span>
                  ) : (
                    <span className="schema-badge optional">Optional</span>
                  )}
                </td>
                <td className="prop-desc">
                  {prop.description || '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function McpCatalog() {
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);
  const [viewMode, setViewMode] = useState('table');

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
              <div 
                key={i} 
                className={`card ${selectedTool?.name === t.name ? 'selected' : ''}`} 
                onClick={() => setSelectedTool(t)}
              >
                <b>{t.name}</b>
                <div className="meta">{t.description}</div>
              </div>
            ))}
          </div>
        </aside>
        <main>
          {!selectedTool ? (
            <div className="empty">MCP Tool을 선택하면 Input / Output Schema를 표 형태로 표시합니다.</div>
          ) : (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: 0 }}>{selectedTool.name}</h2>
                  <p style={{ margin: '4px 0 0', color: '#64748b' }}>{selectedTool.description}</p>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button 
                    className={`btn ${viewMode === 'table' ? 'primary' : 'secondary'}`} 
                    onClick={() => setViewMode('table')}
                    style={{ fontSize: '12px', padding: '6px 12px' }}
                  >
                    📊 Table View
                  </button>
                  <button 
                    className={`btn ${viewMode === 'json' ? 'primary' : 'secondary'}`} 
                    onClick={() => setViewMode('json')}
                    style={{ fontSize: '12px', padding: '6px 12px' }}
                  >
                    JSON View
                  </button>
                </div>
              </div>

              <div className="adminGrid">
                <div className="panel" style={{ margin: 0 }}>
                  <h3>Input Schema</h3>
                  {viewMode === 'table' ? (
                    <SchemaTable schema={selectedTool.input_schema || selectedTool.inputSchema} />
                  ) : (
                    <pre className="schema">{JSON.stringify(selectedTool.input_schema || selectedTool.inputSchema || {}, null, 2)}</pre>
                  )}
                </div>
                <div className="panel" style={{ margin: 0 }}>
                  <h3>Output Schema</h3>
                  {viewMode === 'table' ? (
                    <SchemaTable schema={selectedTool.output_schema || selectedTool.outputSchema} />
                  ) : (
                    <pre className="schema">{JSON.stringify(selectedTool.output_schema || selectedTool.outputSchema || {}, null, 2)}</pre>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
