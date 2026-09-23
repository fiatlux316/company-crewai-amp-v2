
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

export default function CrewProcess() {
  const [crews, setCrews] = useState([]);
  const [selectedCrew, setSelectedCrew] = useState(null);

  const loadCrews = async () => {
    try {
      const data = await api.fetchCrews();
      setCrews(data.crews || []);
    } catch(e) {}
  };

  useEffect(() => {
    loadCrews();
    const timer = setInterval(loadCrews, 3000);
    return () => clearInterval(timer);
  }, []);

  const showCrew = async (c) => {
    setSelectedCrew(c);
    // Real implementation would fetch graph and render D3 here
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
              <div className="meta">{selectedCrew.crew_id} @ {selectedCrew.version}</div>
              <div className="panel wide">
                <h3>Initial Input Parameters</h3>
                <textarea defaultValue={JSON.stringify(selectedCrew.admin?.default_inputs || {}, null, 2)}></textarea>
                <button className="btn secondary">Save Defaults</button>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
