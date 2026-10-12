import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { showAlert, showConfirm } from './Dialog';

export default function ServiceAccessManagement() {
  const [services, setServices] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingServiceId, setEditingServiceId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', description: '', order_num: 0 });

  const loadData = async () => {
    setLoading(true);
    try {
      const [svcData, teamData] = await Promise.all([
        api.fetchAdminServices(),
        api.fetchTeams()
      ]);
      setServices(svcData || []);
      setTeams(teamData || []);
    } catch (err) {
      showAlert('서비스 및 팀 데이터를 불러오는데 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleAccess = async (serviceId, teamId, currentAllowedTeamIds) => {
    const isAllowed = currentAllowedTeamIds.includes(teamId);
    const newAllowed = isAllowed
      ? currentAllowedTeamIds.filter(id => id !== teamId)
      : [...currentAllowedTeamIds, teamId];

    try {
      await api.updateServiceTeamAccess(serviceId, newAllowed);
      setServices(prev => prev.map(s => s.id === serviceId ? { ...s, allowed_team_ids: newAllowed } : s));
    } catch (err) {
      showAlert('권한 변경 중 오류가 발생했습니다: ' + err.message);
    }
  };

  const handleStartEdit = (service) => {
    setEditingServiceId(service.id);
    setEditForm({
      name: service.name,
      description: service.description || '',
      order_num: service.order_num || 0
    });
  };

  const handleSaveEdit = async (serviceId) => {
    try {
      await api.updateService(serviceId, editForm);
      setEditingServiceId(null);
      loadData();
      showAlert('서비스 정보가 저장되었습니다.');
    } catch (err) {
      showAlert('저장 중 오류가 발생했습니다: ' + err.message);
    }
  };

  if (loading) {
    return (
      <section className="view active" style={{ padding: '24px' }}>
        <h2>서비스 및 팀 접근 권한 관리</h2>
        <p>데이터를 로딩 중입니다...</p>
      </section>
    );
  }

  return (
    <section className="view active" style={{ padding: '24px', overflowY: 'auto', height: 'calc(100vh - 110px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0 }}>서비스 및 팀 접근 권한 관리</h2>
          <p className="hint" style={{ margin: '4px 0 0 0', color: '#64748b' }}>
            포탈에 등록된 서비스들의 이름을 수정하고, 각 팀별 접근 권한을 관리합니다.
          </p>
        </div>
        <button className="btn secondary" onClick={loadData}>↻ 새로고침</button>
      </div>

      {/* 1. 서비스 정보 수정 패널 */}
      <div className="panel" style={{ marginBottom: '24px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '16px' }}>🛠 등록된 서비스 목록 ({services.length}개)</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', background: '#f8fafc' }}>
              <th style={{ padding: '10px 12px' }}>서비스 코드</th>
              <th style={{ padding: '10px 12px' }}>서비스 표시명</th>
              <th style={{ padding: '10px 12px' }}>설명</th>
              <th style={{ padding: '10px 12px', width: '80px' }}>순서</th>
              <th style={{ padding: '10px 12px', width: '120px' }}>관리</th>
            </tr>
          </thead>
          <tbody>
            {services.map(s => {
              const isEditing = editingServiceId === s.id;
              return (
                <tr key={s.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#334155' }}>
                    <code>{s.service_code}</code>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                        style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', width: '100%' }}
                      />
                    ) : (
                      <span style={{ fontWeight: '600' }}>{s.name}</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#64748b' }}>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editForm.description}
                        onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                        style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', width: '100%' }}
                      />
                    ) : (
                      s.description || '-'
                    )}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editForm.order_num}
                        onChange={e => setEditForm({ ...editForm, order_num: parseInt(e.target.value) || 0 })}
                        style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', width: '60px' }}
                      />
                    ) : (
                      s.order_num
                    )}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {isEditing ? (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button className="btn primary" onClick={() => handleSaveEdit(s.id)} style={{ padding: '4px 8px', fontSize: '12px' }}>저장</button>
                        <button className="btn secondary" onClick={() => setEditingServiceId(null)} style={{ padding: '4px 8px', fontSize: '12px' }}>취소</button>
                      </div>
                    ) : (
                      <button className="btn secondary" onClick={() => handleStartEdit(s)} style={{ padding: '4px 8px', fontSize: '12px' }}>수정</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 2. 서비스 - 팀 접근 권한 매트릭스 */}
      <div className="panel">
        <h3 style={{ marginTop: 0, marginBottom: '6px', fontSize: '16px' }}>🔐 팀별 서비스 접근 권한 매트릭스</h3>
        <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b' }}>
          체크박스를 클릭하면 해당 팀의 서비스 접근 권한이 즉시 적용됩니다.
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #cbd5e1', background: '#f1f5f9' }}>
                <th style={{ padding: '12px 14px', textAlign: 'left', minWidth: '150px' }}>팀 (Team)</th>
                {services.map(s => (
                  <th key={s.id} style={{ padding: '12px 8px', minWidth: '110px' }}>
                    <div>{s.name}</div>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 'normal' }}>({s.service_code})</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {teams.map(team => (
                <tr key={team.id} style={{ borderBottom: '1px solid #e2e8f0' }} onMouseOver={e => e.currentTarget.style.background = '#f8fafc'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ padding: '12px 14px', textAlign: 'left', fontWeight: '600', color: '#1e293b' }}>
                    🏢 {team.name}
                  </td>
                  {services.map(s => {
                    const isChecked = (s.allowed_team_ids || []).includes(team.id);
                    return (
                      <td key={s.id} style={{ padding: '12px 8px' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleAccess(s.id, team.id, s.allowed_team_ids || [])}
                          style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: '#2563eb' }}
                          title={`${team.name} - ${s.name} 접근 권한 토글`}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
