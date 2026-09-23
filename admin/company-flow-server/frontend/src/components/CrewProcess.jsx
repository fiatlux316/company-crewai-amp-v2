
import React, { useState, useEffect, useRef } from 'react';
import { api } from '../utils/api';

const E = s => String(s ?? '');
const KST = s => {
  if (!s) return '-';
  try {
    const d = new Date(s);
    if (isNaN(d)) return s;
    return d.toLocaleString('ko-KR', {
      timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  } catch (e) { return s; }
};

function CrewDiagram({ graph }) {
  const diagramRef = useRef(null);
  const svgRef = useRef(null);
  const nodesRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (!graph) return;
    renderDiagram();
  }, [graph]);

  const renderDiagram = () => {
    const ns = graph.nodes || [];
    const es = graph.edges || [];
    const pos = {};

    // Layout: task -> agent -> tool columns
    const taskIds = ns.filter(n => n.type === 'task').map(n => n.id);
    const taskOrder = [];
    const incoming = new Set(es.filter(e => e.label === 'next').map(e => e.target));
    const roots = taskIds.filter(id => !incoming.has(id));
    
    function walk(id) {
      if (taskOrder.includes(id)) return;
      taskOrder.push(id);
      es.filter(e => e.source === id && e.label === 'next').forEach(e => walk(e.target));
    }
    roots.forEach(walk);
    taskIds.forEach(walk);

    const taskIndex = Object.fromEntries(taskOrder.map((id, i) => [id, i]));
    ns.filter(n => n.type === 'task').forEach(n => {
      const row = taskIndex[n.id] ?? 0;
      pos[n.id] = { x: 70, y: 55 + row * 180 };
    });
    ns.filter(n => n.type === 'agent').forEach((n, j) => {
      const refs = es.filter(e => e.target === n.id && e.label === 'assigned');
      const row = refs.length ? (taskIndex[refs[0].source] ?? j) : j;
      pos[n.id] = { x: 350, y: 55 + row * 180 };
    });
    const toolRows = {};
    ns.filter(n => n.type === 'tool').forEach((n, j) => {
      const refs = es.filter(e => e.target === n.id && e.label === 'uses');
      const agent = refs[0]?.source;
      const assigned = es.find(e => e.target === agent && e.label === 'assigned');
      const row = assigned ? (taskIndex[assigned.source] ?? j) : j;
      const offset = toolRows[row] || 0;
      toolRows[row] = offset + 1;
      pos[n.id] = { x: 650, y: 55 + row * 180 + offset * 90 };
    });

    const maxY = Math.max(580, ...Object.values(pos).map(p => p.y + 130));
    if (diagramRef.current) diagramRef.current.style.height = maxY + 'px';

    // Render nodes
    if (nodesRef.current) {
      nodesRef.current.innerHTML = ns.map(n => {
        const p = pos[n.id] || { x: 50, y: 50 };
        return `<div class="crewNodeD ${E(n.type)}" style="left:${p.x}px;top:${p.y}px" data-node-id="${E(n.id)}">
          <div class="kind">${E(n.type)}</div>
          <b>${E(n.label)}</b>
          <div class="meta">${E(n.id.split(':').slice(1).join(':'))}</div>
        </div>`;
      }).join('');

      // Add click handlers
      nodesRef.current.querySelectorAll('.crewNodeD').forEach(el => {
        el.addEventListener('click', () => {
          nodesRef.current.querySelectorAll('.crewNodeD').forEach(x => x.classList.remove('active'));
          el.classList.add('active');
          const nodeId = el.dataset.nodeId;
          const node = ns.find(n => n.id === nodeId);
          setSelectedNode(node);
        });
      });
    }

    // Render edges
    if (svgRef.current) {
      const w = diagramRef.current?.clientWidth || 1000;
      const h = maxY;
      svgRef.current.setAttribute('viewBox', `0 0 ${w} ${h}`);
      svgRef.current.innerHTML = `<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>` +
        es.map(e => {
          const a = pos[e.source], b = pos[e.target];
          if (!a || !b) return '';
          let x1 = a.x + 210, y1 = a.y + 37, x2 = b.x, y2 = b.y + 37;
          if (e.label === 'next') { x1 = a.x + 105; y1 = a.y + 74; x2 = b.x + 105; y2 = b.y; }
          const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
          return `<path class="crewEdge ${E(e.label)}" marker-end="url(#arrow)" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}"/>
                  <text class="crewEdgeLabel" x="${mx + 4}" y="${my - 4}">${E(e.label)}</text>`;
        }).join('');
    }
  };

  return (
    <div>
      <div className="crewLegend">
        <span><i className="dot" style={{ background: '#6366f1' }}></i>Task</span>
        <span><i className="dot" style={{ background: '#059669' }}></i>Agent</span>
        <span><i className="dot" style={{ background: '#d97706' }}></i>Tool</span>
      </div>
      <div ref={diagramRef} className="crewDiagram">
        <svg ref={svgRef} className="crewSvg"></svg>
        <div ref={nodesRef} className="crewNodes"></div>
      </div>
      <div className="crewInfo" style={{ marginTop: '12px' }}>
        {selectedNode ? (
          <>
            <h3>{selectedNode.label}</h3>
            <div className="meta">{selectedNode.type} · {selectedNode.id}</div>
            <pre className="schema">{JSON.stringify(selectedNode.detail || {}, null, 2)}</pre>
          </>
        ) : (
          <pre className="schema">노드를 클릭하면 상세 설정을 표시합니다.</pre>
        )}
      </div>
    </div>
  );
}

export default function CrewProcess({ onNavigateHistory }) {
  const [crews, setCrews] = useState([]);
  const [selectedCrew, setSelectedCrew] = useState(null);
  const [graph, setGraph] = useState(null);

  // Settings state
  const [schEnabled, setSchEnabled] = useState(false);
  const [schCron, setSchCron] = useState('');
  const [metaOwner, setMetaOwner] = useState('');
  const [metaDate, setMetaDate] = useState('');
  const [defaultInputs, setDefaultInputs] = useState('{}');

  const loadCrews = async () => {
    try {
      const data = await api.fetchCrews();
      setCrews(data.crews || []);
    } catch (e) {}
  };

  useEffect(() => {
    loadCrews();
    const timer = setInterval(loadCrews, 3000);
    return () => clearInterval(timer);
  }, []);

  const showCrew = async (c) => {
    setSelectedCrew(c);
    const cfg = c.admin || {};
    setSchEnabled(cfg.schedule?.enabled || false);
    setSchCron(cfg.schedule?.cron || '');
    setMetaOwner(c.owner || '');
    setMetaDate(c.deployed_at || '');
    setDefaultInputs(JSON.stringify(cfg.default_inputs || {}, null, 2));

    try {
      const g = await api.fetchGraph(c.crew_id, c.version);
      setGraph(g);
    } catch (e) {
      setGraph(null);
    }
  };

  const saveSettings = async () => {
    if (!selectedCrew) return;
    let inputs;
    try { inputs = JSON.parse(defaultInputs || '{}'); } catch (e) { alert('Input JSON 오류'); return; }
    const body = {
      schedule: { enabled: schEnabled, cron: schCron.trim() },
      default_inputs: inputs,
      metadata: { owner: metaOwner.trim(), deployed_at: metaDate.trim() }
    };
    const r = await api.saveCrewSettings(selectedCrew.crew_id, body);
    if (!r.ok) { alert(await r.text()); return; }
    alert('저장되었습니다.');
    await loadCrews();
  };

  const kickoff = async () => {
    if (!selectedCrew) return;
    if (!confirm(`${selectedCrew.crew_id}@${selectedCrew.version} 을(를) 실행합니다. 저장된 Default Input으로 Kickoff합니다.`)) return;
    try {
      const d = await api.kickoff(selectedCrew.crew_id, selectedCrew.version, { inputs: {} });
      alert('Queued: ' + d.run_id);
      if (onNavigateHistory) onNavigateHistory();
    } catch (e) { alert('Error: ' + e.message); }
  };

  const deleteCrew = async () => {
    if (!selectedCrew) return;
    if (!confirm(`경고: ${selectedCrew.crew_id}@${selectedCrew.version} 배포본을 삭제합니다. Flow에서 참조 중이면 실행이 실패할 수 있습니다. 계속합니까?`)) return;
    const r = await api.deleteCrew(selectedCrew.crew_id, selectedCrew.version);
    if (!r.ok) { alert(await r.text()); return; }
    setSelectedCrew(null);
    setGraph(null);
    await loadCrews();
  };

  return (
    <section id="crew" className="view active">
      <div className="simple">
        <aside>
          <h2>Crew Management</h2>
          <div>
            {crews.map(c => (
              <div key={c.crew_id + c.version} className="card" onClick={() => showCrew(c)}>
                <b>{c.name}</b>
                <div className="meta">{c.crew_id} @ {c.version}</div>
                <div className="meta">{c.owner || ''} · {KST(c.deployed_at)}</div>
              </div>
            ))}
          </div>
        </aside>
        <main>
          {!selectedCrew ? (
            <div className="empty">Crew를 선택하세요.</div>
          ) : (
            <div id="crewDetail">
              <h2>{selectedCrew.name}</h2>
              <div className="meta">{selectedCrew.crew_id} @ {selectedCrew.version} · deployed {KST(selectedCrew.deployed_at)}</div>
              
              <div className="actions" style={{ marginTop: '10px' }}>
                <button className="btn primary" onClick={kickoff}>▶ Kickoff</button>
                <button className="btn danger" onClick={deleteCrew}>Delete Crew</button>
              </div>

              <div className="adminGrid">
                {/* Schedule (Cron) */}
                <div className="panel">
                  <h3>Schedule (Cron)</h3>
                  <label>
                    <input type="checkbox" style={{ width: 'auto' }} checked={schEnabled} onChange={e => setSchEnabled(e.target.checked)} /> Enabled
                  </label>
                  <input value={schCron} onChange={e => setSchCron(e.target.value)} placeholder="*/5 * * * *" />
                  <button className="btn secondary" onClick={saveSettings}>Save Schedule</button>
                  <p className="hint">관리자 상태로 별도 저장되므로 Crew 재배포 시 보존됩니다.</p>
                </div>

                {/* Metadata */}
                <div className="panel">
                  <h3>Metadata</h3>
                  <label>Owner</label>
                  <input value={metaOwner} onChange={e => setMetaOwner(e.target.value)} />
                  <label>Deployment date override</label>
                  <input value={metaDate} onChange={e => setMetaDate(e.target.value)} />
                  <button className="btn secondary" onClick={saveSettings}>Save Metadata</button>
                </div>

                {/* Initial Input Parameters */}
                <div className="panel wide">
                  <h3>Initial Input Parameters</h3>
                  <textarea value={defaultInputs} onChange={e => setDefaultInputs(e.target.value)}></textarea>
                  <button className="btn secondary" onClick={saveSettings}>Save Defaults</button>
                </div>

                {/* Process Diagram */}
                <div className="panel wide">
                  <h3>Task · Agent · Tool Process</h3>
                  {graph ? <CrewDiagram graph={graph} /> : <div className="hint">프로세스 그래프를 로딩 중...</div>}
                </div>

                {/* Execution History link */}
                <div className="panel wide">
                  <h3>Execution History</h3>
                  <div className="historyLink" onClick={() => onNavigateHistory && onNavigateHistory()}>
                    📋 Execution History 탭에서 전체 이력 보기 →
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
