
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../utils/api';

const E = s => String(s ?? '');

export default function NodeFlowDesigner() {
  const [crews, setCrews] = useState([]);
  const [steps, setSteps] = useState([]);
  const [selected, setSelected] = useState(-1);
  const [flowId, setFlowId] = useState('my-flow');
  const [flowName, setFlowName] = useState('My Flow');
  const [flowVersion, setFlowVersion] = useState('1.0.0');
  const [flowDesc, setFlowDesc] = useState('');
  const [savedFlows, setSavedFlows] = useState([]);
  const [status, setStatus] = useState('');
  const [issues, setIssues] = useState('아직 검증하지 않았습니다.');
  const [recs, setRecs] = useState('다른 노드와 연결 추천을 계산할 수 있습니다.');

  const canvasRef = useRef(null);
  const nodesRef = useRef(null);
  const edgesRef = useRef(null);
  const dragRef = useRef(null);

  useEffect(() => {
    api.fetchCrews().then(d => setCrews(d.crews || [])).catch(() => {});
    refreshFlows();
  }, []);

  const refreshFlows = async () => {
    try {
      const d = await (await fetch('/api/v1/flows')).json();
      setSavedFlows(d.flows || []);
    } catch (e) {}
  };

  const getCrew = useCallback((s) => crews.find(c => c.crew_id === s.crew_id && c.version === s.version), [crews]);

  // Render nodes and edges to DOM
  useEffect(() => {
    renderCanvas();
  }, [steps, selected, crews]);

  const renderCanvas = () => {
    if (!nodesRef.current || !edgesRef.current) return;
    
    nodesRef.current.innerHTML = steps.map((s, i) => {
      const c = getCrew(s);
      const ins = c?.input_schema?.properties || {};
      const outs = c?.output_schema?.properties || {};
      return `<div class="node ${i === selected ? 'selected' : ''}" style="left:${s.x}px;top:${s.y}px" data-i="${i}">
        <b>${E(s.step_id)}</b>
        <div class="meta">${E(s.crew_id)} @ ${E(s.version)}</div>
        <div class="portrow">
          <div class="ports">${Object.entries(ins).map(([k, v]) => `<div class="port in">◀ ${E(k)}:${E(v.type || 'any')}</div>`).join('')}</div>
          <div class="ports">${Object.entries(outs).map(([k, v]) => `<div class="port out">${E(k)}:${E(v.type || 'any')} ▶</div>`).join('')}</div>
        </div>
      </div>`;
    }).join('');

    // Add event listeners for nodes
    nodesRef.current.querySelectorAll('.node').forEach(el => {
      const idx = parseInt(el.dataset.i);
      el.addEventListener('click', (e) => { e.stopPropagation(); setSelected(idx); });
      el.addEventListener('mousedown', (e) => startMove(e, idx));
    });

    drawEdges();
  };

  const drawEdges = () => {
    if (!edgesRef.current) return;
    edgesRef.current.innerHTML = '';
    steps.forEach((t, ti) => {
      Object.entries(t.inputs || {}).forEach(([field, val]) => {
        if (typeof val !== 'string' || !val.startsWith('$steps.')) return;
        const p = val.split('.');
        const si = steps.findIndex(s => s.step_id === p[1]);
        if (si < 0) return;
        const a = steps[si];
        const x1 = a.x + 230, y1 = a.y + 55, x2 = t.x, y2 = t.y + 55, m = (x1 + x2) / 2;
        edgesRef.current.innerHTML += `<path class="edge good" d="M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}"/>
          <text class="edgeLabel" x="${m}" y="${(y1 + y2) / 2 - 4}">${E(p.slice(3).join('.'))} → ${E(field)}</text>`;
      });
    });
  };

  const startMove = (e, i) => {
    if (e.button !== 0) return;
    const s = steps[i];
    const sx = e.clientX, sy = e.clientY, ox = s.x, oy = s.y;
    const mv = (ev) => {
      s.x = Math.max(0, ox + ev.clientX - sx);
      s.y = Math.max(0, oy + ev.clientY - sy);
      setSteps([...steps]);
    };
    const up = () => {
      document.removeEventListener('mousemove', mv);
      document.removeEventListener('mouseup', up);
    };
    document.addEventListener('mousemove', mv);
    document.addEventListener('mouseup', up);
  };

  const addCrew = (crewIdx, x = 60, y = 60) => {
    const c = crews[crewIdx];
    const base = c.crew_id.split('.').pop();
    let id = base, n = 2;
    while (steps.some(s => s.step_id === id)) id = base + '-' + n++;
    const newSteps = [...steps, { step_id: id, crew_id: c.crew_id, version: c.version, inputs: {}, continue_on_error: false, x, y }];
    setSteps(newSteps);
    setSelected(newSteps.length - 1);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const i = Number(e.dataTransfer.getData('crew'));
    if (isNaN(i)) return;
    const rect = canvasRef.current.getBoundingClientRect();
    addCrew(i, e.clientX - rect.left + canvasRef.current.scrollLeft, e.clientY - rect.top + canvasRef.current.scrollTop);
  };

  const applyProps = (newStepId, newInputs) => {
    try {
      const updated = [...steps];
      updated[selected].step_id = newStepId.trim();
      updated[selected].inputs = JSON.parse(newInputs || '{}');
      setSteps(updated);
    } catch (e) { alert(e.message); }
  };

  const removeNode = () => {
    const updated = [...steps];
    updated.splice(selected, 1);
    setSteps(updated);
    setSelected(-1);
  };

  const autoLayout = () => {
    const updated = steps.map((s, i) => ({ ...s, x: 80 + (i % 3) * 300, y: 70 + Math.floor(i / 3) * 190 }));
    setSteps(updated);
  };

  const getPayload = () => ({
    flow_id: flowId.trim(), version: flowVersion.trim(), name: flowName.trim(),
    description: flowDesc, steps: steps.map(({ x, y, ...s }) => s), output: {}
  });

  const validateFlow = async () => {
    const d = await (await fetch('/api/v1/flows/validate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(getPayload()) })).json();
    const arr = [...(d.errors || []).map(x => ({ level: 'error', message: x })), ...(d.schema_issues || [])];
    setIssues(arr.length ? arr.map(x => `<div class="issue ${x.level}">${E(x.step_id ? x.step_id + ': ' : '')}${E(x.message)}</div>`).join('') : '<div class="rec">✓ Flow / Schema validation passed</div>');
    setStatus(d.valid ? '✓ Valid' : '✕ Validation failed');
    return d.valid;
  };

  const saveFlow = async () => {
    if (!await validateFlow()) return;
    const p = getPayload();
    const r = await fetch(`/api/v1/flows/${encodeURIComponent(p.flow_id)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) });
    setStatus(r.ok ? '✓ Saved' : 'Save failed');
    if (r.ok) refreshFlows();
  };

  const loadFlow = async (id) => {
    if (!id) return;
    const g = await (await fetch(`/api/v1/flows/${encodeURIComponent(id)}`)).json();
    setFlowId(g.flow_id);
    setFlowName(g.name);
    setFlowVersion(g.version);
    setFlowDesc(g.description || '');
    setSteps(g.nodes.map((n, i) => ({
      step_id: n.id, crew_id: n.crew_id, version: n.version,
      inputs: n.inputs || {}, continue_on_error: false,
      x: 80 + (i % 3) * 300, y: 70 + Math.floor(i / 3) * 190
    })));
    setSelected(-1);
  };

  const newFlow = () => {
    setSteps([]);
    setSelected(-1);
    setFlowId('my-flow');
    setFlowName('My Flow');
    setFlowVersion('1.0.0');
    setFlowDesc('');
    setIssues('아직 검증하지 않았습니다.');
  };

  const selectedStep = selected >= 0 ? steps[selected] : null;
  const selectedStepCrew = selectedStep ? getCrew(selectedStep) : null;

  return (
    <section id="flow" className="view active">
      <div className="designer">
        {/* Crew Catalog Palette */}
        <aside className="palette">
          <h2>Crew Catalog</h2>
          <p className="hint">Canvas로 Drag &amp; Drop 하세요.</p>
          <div>
            {crews.map((c, i) => (
              <div key={c.crew_id + c.version} className="card" draggable="true"
                onDragStart={e => e.dataTransfer.setData('crew', String(i))}>
                <div className="name">{c.name}</div>
                <div className="meta">{c.crew_id} @ {c.version}</div>
                <div className="meta">IN {Object.keys(c.input_schema?.properties || {}).length} · OUT {Object.keys(c.output_schema?.properties || {}).length}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* Workspace Canvas */}
        <div className="workspace">
          <div className="toolbar">
            <button className="btn primary" onClick={newFlow}>New</button>
            <button className="btn secondary" onClick={autoLayout}>Auto Layout</button>
            <button className="btn secondary" onClick={validateFlow}>Validate</button>
            <button className="btn primary" onClick={saveFlow}>Save</button>
            <select style={{ width: '190px', margin: 0 }} onChange={e => loadFlow(e.target.value)} defaultValue="">
              <option value="">Saved flows…</option>
              {savedFlows.map(f => (
                <option key={f.flow_id} value={f.flow_id}>{f.name} ({f.version})</option>
              ))}
            </select>
            <span className="status">{status}</span>
          </div>
          <div ref={canvasRef} className="canvas" onDragOver={e => e.preventDefault()} onDrop={handleDrop}>
            <svg ref={edgesRef} className="edges"></svg>
            <div ref={nodesRef}></div>
          </div>
        </div>

        {/* Properties Panel */}
        <aside className="props">
          <h2>Flow</h2>
          <input value={flowId} onChange={e => setFlowId(e.target.value)} placeholder="Flow ID" />
          <input value={flowName} onChange={e => setFlowName(e.target.value)} placeholder="Name" />
          <input value={flowVersion} onChange={e => setFlowVersion(e.target.value)} placeholder="Version" />
          <textarea value={flowDesc} onChange={e => setFlowDesc(e.target.value)} placeholder="Description"></textarea>
          <hr />
          {selectedStep ? (
            <StepProps
              step={selectedStep}
              crew={selectedStepCrew}
              onApply={applyProps}
              onRemove={removeNode}
              recs={recs}
            />
          ) : (
            <p className="hint">노드를 선택하세요.</p>
          )}
          <hr />
          <h3>Validation</h3>
          <div className="hint" dangerouslySetInnerHTML={{ __html: issues }}></div>
        </aside>
      </div>
    </section>
  );
}

function StepProps({ step, crew, onApply, onRemove, recs }) {
  const [stepId, setStepId] = useState(step.step_id);
  const [inputMap, setInputMap] = useState(JSON.stringify(step.inputs, null, 2));

  useEffect(() => {
    setStepId(step.step_id);
    setInputMap(JSON.stringify(step.inputs, null, 2));
  }, [step]);

  return (
    <div>
      <h3>Step</h3>
      <label>ID</label>
      <input value={stepId} onChange={e => setStepId(e.target.value)} />
      <label>Input Mapping JSON</label>
      <textarea value={inputMap} onChange={e => setInputMap(e.target.value)}></textarea>
      <button className="btn primary" onClick={() => onApply(stepId, inputMap)}>Apply</button>{' '}
      <button className="btn danger" onClick={onRemove}>Remove</button>
      <h3>Schema Recommendations</h3>
      <div className="hint">{recs}</div>
      <h4>Input Schema</h4>
      <pre className="schema">{JSON.stringify(crew?.input_schema || {}, null, 2)}</pre>
      <h4>Output Schema</h4>
      <pre className="schema">{JSON.stringify(crew?.output_schema || {}, null, 2)}</pre>
    </div>
  );
}
