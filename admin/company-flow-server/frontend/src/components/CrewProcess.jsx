
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

const DOW_KR = ['일', '월', '화', '수', '목', '금', '토'];
const describeCron = (expr) => {
  if (!expr || !expr.trim()) return '';
  const parts = expr.trim().split(/\s+/);
  if (parts.length !== 5) return '유효하지 않은 cron 형식';
  const [min, hour, dom, mon, dow] = parts;

  try {
    // Helper: parse */N pattern
    const interval = (f) => { const m = f.match(/^\*\/(\d+)$/); return m ? parseInt(m[1]) : null; };
    const isAny = (f) => f === '*';
    const isNum = (f) => /^\d+$/.test(f);

    const minInt = interval(min);
    const hourInt = interval(hour);

    // Every N minutes
    if (minInt && isAny(hour) && isAny(dom) && isAny(mon) && isAny(dow)) {
      return `매 ${minInt}분마다 실행`;
    }
    // Every N hours
    if (isNum(min) && hourInt && isAny(dom) && isAny(mon) && isAny(dow)) {
      return `매 ${hourInt}시간마다 실행 (${min}분)`;
    }
    if (min === '0' && hourInt && isAny(dom) && isAny(mon) && isAny(dow)) {
      return `매 ${hourInt}시간마다 실행 (정각)`;
    }

    // Specific time, every day
    if (isNum(min) && isNum(hour) && isAny(dom) && isAny(mon) && isAny(dow)) {
      return `매일 ${hour.padStart(2, '0')}:${min.padStart(2, '0')}에 실행`;
    }

    // Specific time, specific day of week
    if (isNum(min) && isNum(hour) && isAny(dom) && isAny(mon) && !isAny(dow)) {
      const days = dow.split(',').map(d => DOW_KR[parseInt(d)] || d).join(', ');
      return `매주 ${days}요일 ${hour.padStart(2, '0')}:${min.padStart(2, '0')}에 실행`;
    }

    // Specific time, specific day of month
    if (isNum(min) && isNum(hour) && isNum(dom) && isAny(mon) && isAny(dow)) {
      return `매월 ${dom}일 ${hour.padStart(2, '0')}:${min.padStart(2, '0')}에 실행`;
    }

    // Every minute
    if (isAny(min) && isAny(hour) && isAny(dom) && isAny(mon) && isAny(dow)) {
      return '매 1분마다 실행';
    }

    // Specific minute every hour
    if (isNum(min) && isAny(hour) && isAny(dom) && isAny(mon) && isAny(dow)) {
      return `매시 ${min}분에 실행`;
    }

    return `${expr}`;
  } catch (e) {
    return expr;
  }
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

    // 1. Determine task order
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

    // 2. Compute dynamic row heights based on item count in each row to prevent overlapping
    const rowCounts = {};
    taskOrder.forEach((taskId, rIdx) => {
      const agents = es.filter(e => e.source === taskId && e.label === 'assigned').map(e => e.target);
      let toolCount = 0;
      agents.forEach(agentId => {
        const tools = es.filter(e => e.source === agentId && e.label === 'uses').map(e => e.target);
        toolCount = Math.max(toolCount, tools.length);
      });
      rowCounts[rIdx] = Math.max(1, agents.length, toolCount);
    });

    const rowYPositions = [];
    let currentY = 40;
    taskOrder.forEach((taskId, rIdx) => {
      rowYPositions[rIdx] = currentY;
      const count = rowCounts[rIdx] || 1;
      currentY += Math.max(130, count * 85 + 30);
    });

    // Column X positions
    const TASK_X = 60;
    const AGENT_X = 350;
    const TOOL_X = 640;

    // Position Tasks
    ns.filter(n => n.type === 'task').forEach(n => {
      const row = taskIndex[n.id] ?? 0;
      pos[n.id] = { x: TASK_X, y: rowYPositions[row] || (40 + row * 130) };
    });

    // Position Agents
    ns.filter(n => n.type === 'agent').forEach((n, j) => {
      const refs = es.filter(e => e.target === n.id && e.label === 'assigned');
      const row = refs.length ? (taskIndex[refs[0].source] ?? j) : j;
      pos[n.id] = { x: AGENT_X, y: rowYPositions[row] || (40 + row * 130) };
    });

    // Position Tools
    const toolRowCounts = {};
    ns.filter(n => n.type === 'tool').forEach((n, j) => {
      const refs = es.filter(e => e.target === n.id && e.label === 'uses');
      const agent = refs[0]?.source;
      const assigned = es.find(e => e.target === agent && e.label === 'assigned');
      const row = assigned ? (taskIndex[assigned.source] ?? j) : j;
      const offset = toolRowCounts[row] || 0;
      toolRowCounts[row] = offset + 1;
      const baseY = rowYPositions[row] || (40 + row * 130);
      pos[n.id] = { x: TOOL_X, y: baseY + offset * 80 };
    });

    const maxY = Math.max(315, currentY + 30);
    if (diagramRef.current) diagramRef.current.style.height = maxY + 'px';

    // 3. Render HTML DOM Nodes
    if (nodesRef.current) {
      nodesRef.current.innerHTML = ns.map(n => {
        const p = pos[n.id] || { x: 50, y: 50 };
        return `<div class="crewNodeD ${E(n.type)}" style="left:${p.x}px;top:${p.y}px" data-node-id="${E(n.id)}">
          <div class="kind">${E(n.type)}</div>
          <b>${E(n.label)}</b>
          <div class="meta">${E(n.id.split(':').slice(1).join(':'))}</div>
        </div>`;
      }).join('');

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

    // 4. Measure actual DOM node dimensions for pixel-perfect arrow alignment
    const bounds = {};
    if (nodesRef.current) {
      nodesRef.current.querySelectorAll('.crewNodeD').forEach(el => {
        const nodeId = el.dataset.nodeId;
        bounds[nodeId] = {
          left: el.offsetLeft,
          top: el.offsetTop,
          width: el.offsetWidth,
          height: el.offsetHeight,
          centerX: el.offsetLeft + el.offsetWidth / 2,
          centerY: el.offsetTop + el.offsetHeight / 2,
          right: el.offsetLeft + el.offsetWidth,
          bottom: el.offsetTop + el.offsetHeight
        };
      });
    }

    // 5. Render SVG Edges perfectly aligned to actual node borders & centers
    const drawEdges = () => {
      const bounds = {};
      if (nodesRef.current) {
        nodesRef.current.querySelectorAll('.crewNodeD').forEach(el => {
          const nodeId = el.dataset.nodeId;
          bounds[nodeId] = {
            left: el.offsetLeft,
            top: el.offsetTop,
            width: el.offsetWidth,
            height: el.offsetHeight,
            centerX: el.offsetLeft + el.offsetWidth / 2,
            centerY: el.offsetTop + el.offsetHeight / 2,
            right: el.offsetLeft + el.offsetWidth,
            bottom: el.offsetTop + el.offsetHeight
          };
        });
      }

      if (svgRef.current) {
        const w = Math.max(diagramRef.current?.clientWidth || 880, 880);
        const h = maxY;
        svgRef.current.setAttribute('viewBox', `0 0 ${w} ${h}`);
        svgRef.current.setAttribute('width', `${w}`);
        svgRef.current.setAttribute('height', `${h}`);
        svgRef.current.setAttribute('preserveAspectRatio', 'none');

        let svgContent = `<defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker>
          <marker id="arrowNext" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/></marker>
        </defs>`;

        svgContent += es.map(e => {
          const a = bounds[e.source] || (pos[e.source] ? {
            left: pos[e.source].x, top: pos[e.source].y, width: 210, height: 74,
            centerX: pos[e.source].x + 105, centerY: pos[e.source].y + 37,
            right: pos[e.source].x + 210, bottom: pos[e.source].y + 74
          } : null);

          const b = bounds[e.target] || (pos[e.target] ? {
            left: pos[e.target].x, top: pos[e.target].y, width: 210, height: 74,
            centerX: pos[e.target].x + 105, centerY: pos[e.target].y + 37,
            right: pos[e.target].x + 210, bottom: pos[e.target].y + 74
          } : null);

          if (!a || !b) return '';

          if (e.label === 'next') {
            // Task-to-task vertical arrow: bottom-center of source → top-center of target
            const x1 = a.centerX, y1 = a.bottom;
            const x2 = b.centerX, y2 = b.top;
            const midY = (y1 + y2) / 2;
            return `<path class="crewEdge next" marker-end="url(#arrowNext)" d="M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}"/>
                    <text class="crewEdgeLabel" x="${(x1 + x2) / 2 + 8}" y="${midY - 3}" style="fill:#6366f1;font-weight:700">next</text>`;
          }

          // assigned / uses horizontal arrow: right side of source → left side of target
          const x1 = a.right;
          const x2 = b.left;

          // Always align horizontal arrows straight at source node's centerY if within target's height bounds
          let y1 = a.centerY;
          let y2 = a.centerY;
          if (a.centerY < b.top || a.centerY > b.bottom) {
            y2 = b.centerY;
          }

          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2;

          if (Math.abs(y1 - y2) < 2) {
            return `<path class="crewEdge ${E(e.label)}" marker-end="url(#arrow)" d="M${x1},${y1} L${x2},${y1}"/>
                    <text class="crewEdgeLabel" x="${mx}" y="${y1 - 5}">${E(e.label)}</text>`;
          }

          return `<path class="crewEdge ${E(e.label)}" marker-end="url(#arrow)" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}"/>
                  <text class="crewEdgeLabel" x="${mx + 4}" y="${my - 4}">${E(e.label)}</text>`;
        }).join('');

        svgRef.current.innerHTML = svgContent;
      }
    };

    drawEdges();
    requestAnimationFrame(drawEdges);
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
    } catch (e) { }
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
    let inputs = {};
    if (defaultInputs && defaultInputs.trim()) {
      try {
        inputs = JSON.parse(defaultInputs);
      } catch (e) {
        alert('Initial Input Parameters JSON 형식이 올바르지 않습니다: ' + e.message);
        return;
      }
    }
    if (!confirm(`${selectedCrew.crew_id}@${selectedCrew.version} 을(를) 실행합니다.`)) return;
    try {
      const d = await api.kickoff(selectedCrew.crew_id, selectedCrew.version, { inputs });
      if (onNavigateHistory) onNavigateHistory(d.run_id);
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

              {/* 1. Schedule (Cron) & Metadata 2-Column Row */}
              <div className="adminGrid">
                {/* Schedule (Cron) */}
                <div className="panel" style={{ margin: 0 }}>
                  <h3>Schedule (Cron)</h3>
                  <label>
                    <input type="checkbox" style={{ width: 'auto' }} checked={schEnabled} onChange={e => setSchEnabled(e.target.checked)} /> Enabled
                  </label>
                  <input value={schCron} onChange={e => setSchCron(e.target.value)} placeholder="*/5 * * * *" />
                  {schCron.trim() && (
                    <p style={{ margin: '0 0 8px', fontSize: '12px', fontWeight: 600, color: '#2563eb' }}>
                      📅 {describeCron(schCron)}
                    </p>
                  )}
                  <button className="btn secondary" onClick={saveSettings}>Save Schedule</button>
                  <p className="hint">관리자 상태로 별도 저장되므로 Crew 재배포 시 보존됩니다.</p>
                </div>

                {/* Metadata */}
                <div className="panel" style={{ margin: 0 }}>
                  <h3>Metadata</h3>
                  <label>Owner</label>
                  <input value={metaOwner} onChange={e => setMetaOwner(e.target.value)} />
                  <label>Deployment Date</label>
                  <input value={metaDate} onChange={e => setMetaDate(e.target.value)} />
                  <button className="btn secondary" onClick={saveSettings}>Save Metadata</button>
                </div>
              </div>

              {/* 2. Initial Input Parameters (Full-Width Single Row) */}
              <div className="panel">
                <h3>Initial Input Parameters</h3>
                <textarea value={defaultInputs} onChange={e => setDefaultInputs(e.target.value)} style={{ minHeight: '160px', fontFamily: 'ui-monospace, monospace' }}></textarea>
                <button className="btn secondary" onClick={saveSettings}>Save Defaults</button>
              </div>

              {/* 3. Task · Agent · Tool Process (Full-Width Single Row) */}
              <div className="panel">
                <h3>Task · Agent · Tool Process</h3>
                {graph ? <CrewDiagram graph={graph} /> : <div className="hint">프로세스 그래프를 로딩 중...</div>}
              </div>

              {/* 4. Execution History Link (Full-Width Single Row) */}
              <div className="panel">
                <h3>Execution History</h3>
                <div className="historyLink" onClick={() => onNavigateHistory && onNavigateHistory()}>
                  📋 Execution History 탭에서 전체 이력 보기 →
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
