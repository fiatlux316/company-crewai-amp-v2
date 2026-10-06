import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { showAlert, showConfirm } from './Dialog';

export default function UserManagement() {
  const [users, setUsers] = useState([]);

  const loadUsers = async () => {
    try {
      const data = await api.fetchUsers();
      setUsers(data);
    } catch (e) {
      await showAlert('유저 목록을 불러오지 못했습니다.');
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleApprove = async (userId) => {
    if (!await showConfirm(`${userId} 사용자를 승인하시겠습니까?`)) return;
    try {
      await api.approveUser(userId);
      await showAlert('승인되었습니다.');
      loadUsers();
    } catch (e) {
      await showAlert(e.message || '승인 중 오류 발생');
    }
  };

  const getTypeLabel = (type) => {
    switch(type) {
      case '1': return 'Strategist';
      case '2': return 'Orchestrator';
      case '3': return 'Doer';
      case '4': return 'Etc';
      default: return 'Unknown';
    }
  };

  return (
    <section className="view active" style={{ padding: '24px' }}>
      <h2>User Management</h2>
      <div className="panel">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
              <th style={{ padding: '12px 8px' }}>사번</th>
              <th style={{ padding: '12px 8px' }}>이름</th>
              <th style={{ padding: '12px 8px' }}>유형</th>
              <th style={{ padding: '12px 8px' }}>가입일</th>
              <th style={{ padding: '12px 8px' }}>상태</th>
              <th style={{ padding: '12px 8px' }}>액션</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.user_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={{ padding: '12px 8px' }}>{u.user_id}</td>
                <td style={{ padding: '12px 8px' }}>{u.name}</td>
                <td style={{ padding: '12px 8px' }}>{getTypeLabel(u.user_type)}</td>
                <td style={{ padding: '12px 8px' }}>{new Date(u.created_at).toLocaleString()}</td>
                <td style={{ padding: '12px 8px' }}>{u.status === '1' ? '승인됨' : '미승인'}</td>
                <td style={{ padding: '12px 8px' }}>
                  {u.status === '0' && (
                    <button className="btn primary" onClick={() => handleApprove(u.user_id)}>승인</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
