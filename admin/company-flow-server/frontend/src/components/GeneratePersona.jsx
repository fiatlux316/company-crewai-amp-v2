
import React, { useState } from 'react';
import { api } from '../utils/api';

export default function GeneratePersona({ onKickoff }) {
  const [goal, setGoal] = useState('');
  const [steps, setSteps] = useState({
    extract: { name: '추출', checked: true, tools: [] },
    analysis: { name: '분석', checked: true, tools: [] },
    write: { name: '작성', checked: true, tools: [] },
    report: { name: '보고', checked: true, tools: [] }
  });

  const availableTools = ['jira', 'confluence', 'rds', 'datadog', 'outlook', 'teams'];
  const colors = { extract: '#6366f1', analysis: '#059669', write: '#d97706', report: '#db2777' };

  const handleStepToggle = (stepId) => {
    setSteps(prev => ({ ...prev, [stepId]: { ...prev[stepId], checked: !prev[stepId].checked } }));
  };

  const handleToolToggle = (stepId, tool) => {
    setSteps(prev => {
      const currentTools = prev[stepId].tools;
      const newTools = currentTools.includes(tool) 
        ? currentTools.filter(t => t !== tool)
        : [...currentTools, tool];
      return { ...prev, [stepId]: { ...prev[stepId], tools: newTools } };
    });
  };

  const submitPersona = async () => {
    if (!goal.trim()) return alert("업무 목적을 입력하세요.");
    
    let stepTools = [];
    Object.entries(steps).forEach(([id, config]) => {
      if (config.checked) {
        stepTools.push(`${id}:${config.tools.join(',')}`);
      }
    });

    if (stepTools.length === 0) return alert("최소 하나 이상의 단계를 선택하세요.");

    try {
      const { crews } = await api.fetchCrews();
      const targetCrew = crews.find(c => c.crew_id === 'ops.persona_generate');
      
      if (!targetCrew) return alert("ops.persona_generate 크루를 찾을 수 없습니다.");

      const payload = { inputs: { business_goal: goal, step_tools: stepTools } };
      if(!window.confirm(`업무목적:\n${goal}\n\n단계별 도구:\n${stepTools.join('\n')}\n\n진행하시겠습니까?`)) return;

      const res = await api.kickoff(targetCrew.crew_id, targetCrew.version, payload);
      alert('Queued: ' + res.run_id);
      onKickoff();
    } catch (e) {
      alert("Error: " + e.message);
    }
  };

  return (
    <section id="persona" className="view active" style={{ padding: '24px', overflow: 'auto', height: 'calc(100vh)' }}>
      <h2 style={{ marginTop: 0, marginBottom: '4px' }}>Generate Persona</h2>
      <p className="hint" style={{ marginTop: 0, marginBottom: '24px' }}>업무 목적과 단계별 사용 도구를 매핑하여 Persona Crew를 생성합니다.</p>

      <div className="panel wide">
        <h3>1. 업무목적 (Business Goal)</h3>
        <textarea 
          value={goal} 
          onChange={e => setGoal(e.target.value)} 
          placeholder="이 페르소나가 수행해야 할 업무 목적을 상세히 입력하세요."
        ></textarea>
      </div>

      <div className="panel wide">
        <h3>2. 단계별 도구 (Step Tools)</h3>
        <div id="stepToolsContainer">
          {Object.entries(steps).map(([id, config]) => (
            <div key={id} className="step-group" style={{ marginBottom: id !== 'report' ? '15px' : '0', borderLeft: `3px solid ${colors[id]}`, paddingLeft: '10px', display: 'flex', alignItems: 'center', gap: '20px' }}>
              <label style={{ fontWeight: 'bold', cursor: 'pointer', width: '140px', flexShrink: 0 }}>
                <input type="checkbox" checked={config.checked} onChange={() => handleStepToggle(id)} /> {config.name} ({id})
              </label>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {availableTools.map(tool => (
                  <label key={tool}>
                    <input 
                      type="checkbox" 
                      value={tool} 
                      disabled={!config.checked}
                      checked={config.tools.includes(tool)}
                      onChange={() => handleToolToggle(id, tool)}
                    /> {tool}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="actions" style={{ marginTop: '20px' }}>
        <button className="btn primary" onClick={submitPersona}>▶ Generate Persona Crew</button>
      </div>
    </section>
  );
}
