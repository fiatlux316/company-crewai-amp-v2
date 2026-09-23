import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

function SchemaTable({ schema }) {
  if (!schema || typeof schema !== 'object') {
    return <div className="hint">정의된 스키마가 없습니다.</div>;
  }

  let props = {};
  let requiredList = [];

  if (schema.properties && typeof schema.properties === 'object') {
    props = schema.properties;
    requiredList = Array.isArray(schema.required) ? schema.required : [];
  } else if (schema.type === 'object' && schema.properties) {
    props = schema.properties;
    requiredList = Array.isArray(schema.required) ? schema.required : [];
  } else if (schema.type && typeof schema.type === 'string') {
    // Single-type schema definition
    props = {
      result: {
        type: schema.type,
        description: schema.description || 'Output result'
      }
    };
  } else {
    // Check if top-level keys are property definitions
    const keys = Object.keys(schema);
    if (keys.length > 0) {
      props = schema;
    }
  }

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
            const rawProp = props[key];
            const prop = typeof rawProp === 'object' && rawProp !== null ? rawProp : { type: String(rawProp) };
            const isRequired = requiredList.includes(key);
            const typeStr = prop.type ? (Array.isArray(prop.type) ? prop.type.join(' | ') : prop.type) : (typeof rawProp === 'string' ? rawProp : 'any');

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

function getInitialArgs(schema) {
  if (!schema) return {};
  const props = schema.properties || (schema.type === 'object' ? schema.properties : null);
  if (!props) return {};
  const initial = {};
  Object.keys(props).forEach(key => {
    const propDef = props[key];
    if (propDef && propDef.default !== undefined) {
      initial[key] = propDef.default;
    } else if (propDef && (propDef.type === 'integer' || propDef.type === 'number')) {
      initial[key] = 0;
    } else if (propDef && propDef.type === 'boolean') {
      initial[key] = false;
    } else if (propDef && propDef.type === 'array') {
      initial[key] = [];
    } else if (propDef && propDef.type === 'object') {
      initial[key] = {};
    } else {
      initial[key] = '';
    }
  });
  return initial;
}

export default function McpCatalog() {
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);
  const [viewMode, setViewMode] = useState('table');

  // Connection Test States
  const [testArgs, setTestArgs] = useState({});
  const [testJson, setTestJson] = useState('{}');
  const [testInputMode, setTestInputMode] = useState('form');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    api.fetchMcpTools().then(d => setTools(d.tools)).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedTool) {
      const initial = getInitialArgs(selectedTool.input_schema || selectedTool.inputSchema);
      setTestArgs(initial);
      setTestJson(JSON.stringify(initial, null, 2));
      setTestResult(null);
      setIsTesting(false);
    }
  }, [selectedTool]);

  const handleRunTest = async () => {
    if (!selectedTool) return;
    setIsTesting(true);
    setTestResult(null);

    let payloadArgs = {};
    try {
      if (testInputMode === 'json') {
        payloadArgs = JSON.parse(testJson);
      } else {
        payloadArgs = { ...testArgs };
      }
    } catch (err) {
      setTestResult({
        status: 'error',
        error: 'JSON 입력 형식이 올바르지 않습니다: ' + err.message,
        executed_at: new Date().toISOString()
      });
      setIsTesting(false);
      return;
    }

    try {
      const res = await api.testMcpTool(selectedTool.name, payloadArgs);
      setTestResult(res);
    } catch (err) {
      setTestResult({
        status: 'error',
        error: err.toString(),
        executed_at: new Date().toISOString()
      });
    } finally {
      setIsTesting(false);
    }
  };

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
            <div className="empty">MCP Tool을 선택하면 Input / Output Schema 및 접속 테스트 기능을 사용할 수 있습니다.</div>
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

              {/* MCP Tool Connection Test Section */}
              <div className="panel" style={{ marginTop: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    ⚡ MCP Tool 접속 테스트
                  </h3>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button 
                      type="button"
                      className={`btn ${testInputMode === 'form' ? 'primary' : 'secondary'}`}
                      onClick={() => setTestInputMode('form')}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      Form Input
                    </button>
                    <button 
                      type="button"
                      className={`btn ${testInputMode === 'json' ? 'primary' : 'secondary'}`}
                      onClick={() => setTestInputMode('json')}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      JSON Input
                    </button>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: '#64748b', marginTop: 0, marginBottom: '14px' }}>
                  선택된 MCP Tool(<code>{selectedTool.name}</code>)에 파라미터를 입력한 후 [접속테스트] 버튼을 클릭하여 서버 호출 결과를 확인합니다.
                </p>

                {/* Parameters Form / JSON Editor */}
                <div style={{ marginBottom: '16px' }}>
                  {testInputMode === 'form' ? (
                    Object.keys(testArgs).length > 0 ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
                        {Object.keys(testArgs).map(key => {
                          const schemaProps = (selectedTool.input_schema || selectedTool.inputSchema)?.properties || {};
                          const propDef = schemaProps[key] || {};
                          const isReq = Array.isArray((selectedTool.input_schema || selectedTool.inputSchema)?.required) &&
                                        (selectedTool.input_schema || selectedTool.inputSchema).required.includes(key);
                          return (
                            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              <label style={{ fontSize: '12px', fontWeight: 600, color: '#334155' }}>
                                {key} {isReq && <span style={{ color: '#ef4444' }}>*</span>}
                                {propDef.type && <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: '4px' }}>({propDef.type})</span>}
                              </label>
                              <input
                                type={propDef.type === 'integer' || propDef.type === 'number' ? 'number' : 'text'}
                                value={testArgs[key]}
                                placeholder={propDef.description || key}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  const updated = { ...testArgs, [key]: val };
                                  setTestArgs(updated);
                                  setTestJson(JSON.stringify(updated, null, 2));
                                }}
                                style={{ margin: 0 }}
                              />
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="hint">입력 파라미터(properties)가 없는 툴입니다. 바로 접속테스트를 수행할 수 있습니다.</div>
                    )
                  ) : (
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: 600, color: '#334155', display: 'block', marginBottom: '6px' }}>
                        Arguments (JSON Format)
                      </label>
                      <textarea
                        rows={5}
                        value={testJson}
                        onChange={(e) => {
                          setTestJson(e.target.value);
                          try {
                            setTestArgs(JSON.parse(e.target.value));
                          } catch (_) {}
                        }}
                        style={{ fontFamily: 'monospace', fontSize: '13px', margin: 0 }}
                      />
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: (testResult || isTesting) ? '16px' : '0' }}>
                  <button 
                    className="btn primary" 
                    onClick={handleRunTest}
                    disabled={isTesting}
                    style={{ padding: '8px 18px', fontSize: '13px' }}
                  >
                    {isTesting ? '⏳ 접속 테스트 중...' : '▶ 접속테스트'}
                  </button>
                </div>

                {/* Test Output Console */}
                {(isTesting || testResult) && (
                  <div style={{ marginTop: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h4 style={{ margin: 0, fontSize: '13px', color: '#334155' }}>실행 결과 (Execution Output)</h4>
                      {testResult && (
                        <span className={`schema-badge ${testResult.status === 'error' ? 'required' : 'optional'}`} style={{ textTransform: 'uppercase' }}>
                          {testResult.status || 'DONE'}
                        </span>
                      )}
                    </div>

                    {isTesting ? (
                      <div className="hint">MCP 서버를 호출하고 있습니다...</div>
                    ) : (
                      <pre className="verboseLive" style={{ maxHeight: '250px', overflowY: 'auto', background: '#0f172a', color: '#38bdf8', padding: '12px', borderRadius: '8px', fontSize: '12px', margin: 0 }}>
                        {JSON.stringify(testResult, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
