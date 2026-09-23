
import React, { useState } from 'react';
import { api } from '../utils/api';

export default function GeneratePersona({ onKickoff }) {
  const [personaName, setPersonaName] = useState('');
  const [goal, setGoal] = useState('');
  const [steps, setSteps] = useState({
    extract: { name: '추출', checked: true, tools: [] },
    analysis: { name: '분석', checked: true, tools: [] },
    write: { name: '작성', checked: true, tools: [] },
    report: { name: '보고', checked: true, tools: [] }
  });

  const stepAvailableTools = {
    extract: ['jira', 'confluence', 'database', 'datadog', 'repositories'],
    analysis: [],
    write: ['jira', 'confluence'],
    report: ['teams', 'outlook']
  };
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
    if (!personaName.trim()) return alert("Persona 이름을 입력하세요.");
    if (!goal.trim()) return alert("업무 목적을 입력하세요.");

    let stepTools = [];
    Object.entries(steps).forEach(([id, config]) => {
      if (config.checked) {
        if (config.tools.length > 1) {
          stepTools.push(`${id}:[${config.tools.join(',')}]`);
        } else if (config.tools.length === 1) {
          stepTools.push(`${id}:${config.tools[0]}`);
        } else {
          stepTools.push(`${id}`);
        }
      }
    });

    if (stepTools.length === 0) return alert("최소 하나 이상의 단계를 선택하세요.");

    try {
      const { crews } = await api.fetchCrews();
      const targetCrew = crews.find(c => c.crew_id === 'ops.persona_generate');

      if (!targetCrew) return alert("ops.persona_generate 크루를 찾을 수 없습니다.");

      const payload = { inputs: { persona_name: personaName, business_goal: goal, step_tools: stepTools } };
      if (!window.confirm(`Persona 이름:\n${personaName}\n\n업무목적:\n${goal}\n\n단계별 도구:\n${stepTools.join('\n')}\n\n진행하시겠습니까?`)) return;

      const res = await api.kickoff(targetCrew.crew_id, targetCrew.version, payload);
      onKickoff(res.run_id);
    } catch (e) {
      alert("Error: " + e.message);
    }
  };

  return (
    <section id="persona" className="view active" style={{ padding: '24px', overflow: 'auto', height: 'calc(100vh)' }}>
      <h2 style={{ marginTop: 0, marginBottom: '4px' }}>Generate Persona</h2>
      <p className="hint" style={{ marginTop: 0, marginBottom: '24px' }}>업무 목적과 단계별 사용 도구를 매핑하여 Persona Crew를 생성합니다.</p>

      <div className="panel wide">
        <h3>1. Persona 이름 (Persona Name)</h3>
        <input
          type="text"
          value={personaName}
          onChange={e => setPersonaName(e.target.value)}
          placeholder="생성할 페르소나 이름을 입력하세요 (예: DevOps 엔지니어, QA 테스트 관리자)"
          style={{ width: '100%', padding: '10px 12px', fontSize: '14px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
        />
      </div>

      <div className="panel wide">
        <h3>2. 업무목적 (Business Goal)</h3>
        <textarea
          value={goal}
          onChange={e => setGoal(e.target.value)}
          placeholder="이 페르소나가 수행해야 할 업무 목적을 상세히 입력하세요."
        ></textarea>
      </div>

      <div className="panel wide">
        <h3>
          3. 단계별 도구 (Step Tools)
          <span style={{ display: 'block', fontSize: '50%', fontWeight: 'normal', color: '#64748b', marginTop: '4px' }}>
            * 불필요한 단계는 체크 해제해 주세요. 선택된 도구에 맞는 mcp tools 을 자동으로 추천해 줍니다.
          </span>
        </h3>

        {/* 프로세스 순차 진행 도식화 배너 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '20px',
          padding: '12px 16px',
          backgroundColor: '#f8fafc',
          borderRadius: '10px',
          border: '1px solid #e2e8f0',
          overflowX: 'auto'
        }}>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', marginRight: '4px', flexShrink: 0 }}>
            프로세스 순차 흐름:
          </span>
          {Object.entries(steps).map(([id, config], index, arr) => (
            <React.Fragment key={id}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '20px',
                backgroundColor: config.checked ? `${colors[id]}15` : '#f1f5f9',
                border: `1.5px solid ${config.checked ? colors[id] : '#cbd5e1'}`,
                color: config.checked ? colors[id] : '#94a3b8',
                fontWeight: 'bold',
                fontSize: '13px',
                whiteSpace: 'nowrap'
              }}>
                <span style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: config.checked ? colors[id] : '#cbd5e1',
                  color: '#ffffff',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  flexShrink: 0
                }}>{index + 1}</span>
                <span>{config.name} ({id})</span>
              </div>
              {index < arr.length - 1 && (
                <span style={{ color: '#6366f1', fontWeight: 'bold', fontSize: '16px', flexShrink: 0 }}>➔</span>
              )}
            </React.Fragment>
          ))}
        </div>

        <div id="stepToolsContainer">
          {Object.entries(steps).map(([id, config], index, arr) => (
            <React.Fragment key={id}>
              <div className="step-group" style={{
                borderLeft: `4px solid ${config.checked ? colors[id] : '#cbd5e1'}`,
                paddingLeft: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                paddingTop: '8px',
                paddingBottom: '8px',
                backgroundColor: config.checked ? 'transparent' : '#f9fafb',
                borderRadius: '0 8px 8px 0'
              }}>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', cursor: 'pointer', width: '150px', flexShrink: 0 }}>
                  <input
                    type="checkbox"
                    checked={config.checked}
                    onChange={() => handleStepToggle(id)}
                    style={{ margin: 0, width: '16px', height: '16px', cursor: 'pointer' }}
                  />
                  <span>{config.name} ({id})</span>
                </label>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {(stepAvailableTools[id] || []).length === 0 ? (
                    <span style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>해당 없음</span>
                  ) : (
                    stepAvailableTools[id].map(tool => (
                      <label key={tool} style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', cursor: config.checked ? 'pointer' : 'not-allowed', color: config.checked ? '#374151' : '#9ca3af' }}>
                        <input
                          type="checkbox"
                          value={tool}
                          disabled={!config.checked}
                          checked={config.tools.includes(tool)}
                          onChange={() => handleToolToggle(id, tool)}
                          style={{ margin: 0, cursor: config.checked ? 'pointer' : 'not-allowed' }}
                        />
                        <span>{tool}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
              {index < arr.length - 1 && (
                <div style={{ paddingLeft: '10px', height: '22px', display: 'flex', alignItems: 'center', color: '#6366f1', fontSize: '14px', fontWeight: 'bold' }}>
                  <span style={{ marginLeft: '-4px' }}>↓</span>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="actions" style={{ marginTop: '20px' }}>
        <button className="btn primary" onClick={submitPersona}>▶ Generate Persona Crew</button>
      </div>
    </section>
  );
}
