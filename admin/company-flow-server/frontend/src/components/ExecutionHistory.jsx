
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

const E = s => String(s??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KST = s => {
  if(!s) return '-';
  try {
    let d = new Date(s);
    if(isNaN(d)) return s;
    return d.toLocaleString('ko-KR', {timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false});
  } catch(e) { return s; }
};

export default function ExecutionHistory({ initialRunId }) {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(initialRunId || null);
  const [currentRun, setCurrentRun] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchRunDetail = async (id) => {
    if (!id) return;
    try {
      const data = await api.fetchRun(id);
      setCurrentRun(data);
    } catch(e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (initialRunId) {
      setSelectedRunId(initialRunId);
      fetchRunDetail(initialRunId);
    }
  }, [initialRunId]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api.fetchRuns();
      setRuns(data.runs || []);
    } catch(e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    const refreshAll = async () => {
      try {
        const data = await api.fetchRuns();
        setRuns(data.runs || []);
      } catch(e) {
        console.error(e);
      }
      if (selectedRunId) {
        try {
          const runData = await api.fetchRun(selectedRunId);
          setCurrentRun(runData);
        } catch(e) {
          console.error(e);
        }
      }
    };

    refreshAll();
    const timer = setInterval(refreshAll, 2000);
    return () => clearInterval(timer);
  }, [selectedRunId]);

  const selectRun = async (id) => {
    setSelectedRunId(id);
    await fetchRunDetail(id);
  };

  const handleManualRefresh = async () => {
    await loadHistory();
    if (selectedRunId) {
      await fetchRunDetail(selectedRunId);
    }
  };

  const deleteHistory = async (id) => {
    if(!window.confirm('경고: 이 실행 이력을 영구 삭제합니다. 계속합니까?')) return;
    try {
      await api.deleteRun(id);
      setSelectedRunId(null);
      setCurrentRun(null);
      loadHistory();
    } catch(e) {
      alert(e.message);
    }
  };

  return (
    <section id="history" className="view active">
      <div className="simple historyList">
        <aside>
          <h2>Execution History</h2>
          <div style={{padding: '0 4px 8px'}}>
            <button className="btn secondary" onClick={handleManualRefresh} style={{width: '100%'}}>↻ Refresh</button>
          </div>
          <div id="historyRunList">
            {runs.length === 0 && <div className="empty" style={{padding: '40px'}}>실행 이력이 없습니다.</div>}
            {runs.map(r => (
              <div key={r.run_id} className={`runItem ${currentRun?.run_id === r.run_id ? 'selected' : ''}`} onClick={() => selectRun(r.run_id)}>
                <span className={`badge ${r.status}`}>{r.status}</span> <span style={{fontWeight: 600}}>{r.crew_id}</span>
                <div className="meta">{r.trigger} · {KST(r.created_at)}</div>
                <div className="meta" style={{fontSize: '10px', color: '#9ca3af'}}>{r.run_id}</div>
              </div>
            ))}
          </div>
        </aside>
        <main>
          {!currentRun ? (
            <div className="empty">실행 이력을 선택하세요.</div>
          ) : (
            <div>
              <div style={{display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap'}}>
                <h2 style={{margin: 0}}>Run Detail</h2>
                <span className={`badge ${currentRun.status}`}>{currentRun.status}</span>
                {(currentRun.status === 'running' || currentRun.status === 'queued') && <span className="liveTag">Live</span>}
                <div style={{marginLeft: 'auto'}}>
                  <button className="btn danger" onClick={() => deleteHistory(currentRun.run_id)}>Delete</button>
                </div>
              </div>
              <div className="runMeta">
                <span>📦 {currentRun.crew_id} @ {currentRun.version}</span>
                <span>🔀 {currentRun.trigger}</span>
                <span>📅 {KST(currentRun.created_at)}</span>
                {currentRun.started_at && <span>▶ {KST(currentRun.started_at)}</span>}
                {currentRun.ended_at && <span>⏹ {KST(currentRun.ended_at)}</span>}
              </div>
              <div className="meta" style={{marginBottom: '12px', fontSize: '10px', color: '#9ca3af'}}>{currentRun.run_id}</div>
              <div className="panel">
                <h3>Inputs</h3>
                <pre className="schema">{JSON.stringify(currentRun.inputs, null, 2)}</pre>
              </div>
              <div className="panel">
                <h3>Outputs</h3>
                <pre className="schema" style={{ maxHeight: '400px', overflowY: 'auto' }}>{JSON.stringify(currentRun.outputs, null, 2)}</pre>
              </div>
              {currentRun.error && (
                <div className="panel">
                  <h3 style={{color: '#991b1b'}}>Error</h3>
                  <pre className="verbose">{currentRun.error}</pre>
                </div>
              )}
              {currentRun.artifacts && currentRun.artifacts.length > 0 && (
                <div className="panel">
                  <h3>Generated Artifacts (산출물 파일)</h3>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                    {currentRun.artifacts.map((art) => (
                      <a
                        key={art.filename}
                        href={`/api/v1/runs/${currentRun.run_id}/artifacts/${art.filename}`}
                        download
                        className="btn secondary"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', textDecoration: 'none' }}
                      >
                        📥 {art.filename} <span style={{ fontSize: '11px', color: '#6b7280' }}>({(art.size / 1024).toFixed(1)} KB)</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
              <div className="panel">
                <h3>Verbose Log</h3>
                <pre className="verboseLive">{(currentRun.verbose || []).join('\n')}</pre>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
