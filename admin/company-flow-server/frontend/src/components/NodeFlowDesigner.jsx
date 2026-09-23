
import React from 'react';

export default function NodeFlowDesigner() {
  return (
    <section id="flow" className="view active">
      <div className="designer">
        <aside className="palette">
          <h2>Crew Catalog</h2>
          <p className="hint">Canvas로 Drag & Drop 하세요.</p>
        </aside>
        <div className="workspace">
          <div className="toolbar">
            <button className="btn primary">New</button>
          </div>
          <div className="canvas">
             <div className="empty">Flow Designer (React Port in Progress)</div>
          </div>
        </div>
        <aside className="props">
          <h2>Flow Properties</h2>
        </aside>
      </div>
    </section>
  );
}
