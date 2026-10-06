import React, { useState } from 'react';
import { api } from '../utils/api';
import { showAlert } from './Dialog';

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [userType, setUserType] = useState('3');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isLogin) {
        const res = await api.login(userId, password);
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('user_id', res.user_id);
        localStorage.setItem('user_type', res.user_type);
        localStorage.setItem('user_name', res.name);
        onLogin();
      } else {
        await api.signup({ user_id: userId, name, password, user_type: userType });
        await showAlert('가입 신청이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.');
        setIsLogin(true);
      }
    } catch (err) {
      await showAlert(err.message || '오류가 발생했습니다.');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', width: '100%', background: '#f8fafc' }}>
      <form onSubmit={handleSubmit} className="panel" style={{ width: '400px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '10px' }}>{isLogin ? '로그인' : '회원가입'}</h2>
        
        <div>
          <label>사번 (6자리 숫자)</label>
          <input type="text" value={userId} onChange={e => setUserId(e.target.value)} required pattern="\d{6}" maxLength="6" />
        </div>

        {!isLogin && (
          <div>
            <label>이름</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required />
          </div>
        )}

        <div>
          <label>비밀번호</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>

        {!isLogin && (
          <div>
            <label>사용자 유형</label>
            <select value={userType} onChange={e => setUserType(e.target.value)}>
              <option value="1">Strategist</option>
              <option value="2">Orchestrator</option>
              <option value="3">Doer</option>
              <option value="4">Etc</option>
            </select>
          </div>
        )}

        <button type="submit" className="btn primary" style={{ marginTop: '10px', justifyContent: 'center' }}>
          {isLogin ? '로그인' : '가입하기'}
        </button>

        <div style={{ textAlign: 'center', marginTop: '10px' }}>
          <a href="#" onClick={(e) => { e.preventDefault(); setIsLogin(!isLogin); }} style={{ color: '#2563eb', textDecoration: 'none', fontSize: '14px' }}>
            {isLogin ? '계정이 없으신가요? 회원가입' : '이미 계정이 있으신가요? 로그인'}
          </a>
        </div>
      </form>
    </div>
  );
}
