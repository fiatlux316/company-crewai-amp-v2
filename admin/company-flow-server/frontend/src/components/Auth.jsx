import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { showAlert } from './Dialog';

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [userType, setUserType] = useState('3');
  const [teamId, setTeamId] = useState('');
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    api.fetchTeams()
      .then(data => {
        setTeams(data || []);
        if (data && data.length > 0) {
          setTeamId(data[0].id);
        }
      })
      .catch(err => console.error("Failed to load teams:", err));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isLogin) {
        const res = await api.login(userId, password);
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('user_id', res.user_id);
        localStorage.setItem('user_type', res.user_type);
        localStorage.setItem('user_name', res.name);
        if (res.team_id) localStorage.setItem('team_id', res.team_id);
        else localStorage.removeItem('team_id');
        if (res.team_name) localStorage.setItem('team_name', res.team_name);
        else localStorage.removeItem('team_name');
        onLogin();
      } else {
        if (!teamId) {
          await showAlert('소속 팀을 선택해주세요.');
          return;
        }
        await api.signup({ user_id: userId, name, password, user_type: userType, team_id: teamId });
        await showAlert('가입 신청이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.');
        setIsLogin(true);
      }
    } catch (err) {
      await showAlert(err.message || '오류가 발생했습니다.');
    }
  };

  return (
    <div style={{
      position: 'relative',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      width: '100%',
      backgroundImage: `linear-gradient(rgba(10, 15, 29, 0.65), rgba(10, 15, 29, 0.78)), url('/images/login-bg.png')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
    }}>
      {/* Background ambient glow effect */}
      <div style={{
        position: 'absolute',
        width: '500px',
        height: '500px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, rgba(99, 102, 241, 0.05) 50%, transparent 70%)',
        filter: 'blur(40px)',
        pointerEvents: 'none'
      }} />

      <form onSubmit={handleSubmit} style={{
        position: 'relative',
        width: '400px',
        background: 'rgba(15, 23, 42, 0.78)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '16px',
        padding: '32px 36px',
        boxShadow: '0 20px 45px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        zIndex: 10
      }}>
        {/* Portal Branding */}
        <div style={{ textAlign: 'center', marginBottom: '22px', width: '100%' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '6px'
          }}>
            <span style={{
              fontSize: '22px',
              fontWeight: '800',
              letterSpacing: '-0.5px',
              background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              AI Native Works
            </span>
          </div>
          <p style={{
            fontSize: '12px',
            color: '#94a3b8',
            margin: '2px 0 0',
            letterSpacing: '0.2px'
          }}>
            Next-Gen Intelligent Multi-Agent Workplace
          </p>
        </div>

        <div style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          paddingBottom: '12px',
          marginBottom: '18px'
        }}>
          <span style={{ fontSize: '15px', fontWeight: '700', color: '#f1f5f9' }}>
            {isLogin ? '로그인' : '회원가입'}
          </span>
        </div>

        {/* 70% 크기로 줄인 입력 컨트롤 영역 */}
        <div style={{
          width: '70%',
          display: 'flex',
          flexDirection: 'column',
          gap: '11px'
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '4px' }}>
              사번 (6자리)
            </label>
            <input
              type="text"
              value={userId}
              onChange={e => setUserId(e.target.value)}
              required
              pattern="\d{6}"
              maxLength="6"
              placeholder="사번 입력"
              style={{
                width: '100%',
                padding: '7px 10px',
                fontSize: '12px',
                background: 'rgba(30, 41, 59, 0.7)',
                color: '#f8fafc',
                border: '1px solid rgba(148, 163, 184, 0.25)',
                borderRadius: '6px',
                outline: 'none',
                boxSizing: 'border-box',
                margin: 0
              }}
            />
          </div>

          {!isLogin && (
            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '4px' }}>
                이름
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                placeholder="이름 입력"
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  fontSize: '12px',
                  background: 'rgba(30, 41, 59, 0.7)',
                  color: '#f8fafc',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  borderRadius: '6px',
                  outline: 'none',
                  boxSizing: 'border-box',
                  margin: 0
                }}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '4px' }}>
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="비밀번호 입력"
              style={{
                width: '100%',
                padding: '7px 10px',
                fontSize: '12px',
                background: 'rgba(30, 41, 59, 0.7)',
                color: '#f8fafc',
                border: '1px solid rgba(148, 163, 184, 0.25)',
                borderRadius: '6px',
                outline: 'none',
                boxSizing: 'border-box',
                margin: 0
              }}
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '4px' }}>
                  소속 팀
                </label>
                <select
                  value={teamId}
                  onChange={e => setTeamId(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    fontSize: '12px',
                    background: 'rgba(30, 41, 59, 0.9)',
                    color: '#f8fafc',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    borderRadius: '6px',
                    outline: 'none',
                    boxSizing: 'border-box',
                    margin: 0
                  }}
                >
                  {teams.map(t => (
                    <option key={t.id} value={t.id} style={{ background: '#1e293b', color: '#fff' }}>{t.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '4px' }}>
                  사용자 유형
                </label>
                <select
                  value={userType}
                  onChange={e => setUserType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    fontSize: '12px',
                    background: 'rgba(30, 41, 59, 0.9)',
                    color: '#f8fafc',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    borderRadius: '6px',
                    outline: 'none',
                    boxSizing: 'border-box',
                    margin: 0
                  }}
                >
                  <option value="1" style={{ background: '#1e293b', color: '#fff' }}>Strategist</option>
                  <option value="2" style={{ background: '#1e293b', color: '#fff' }}>Orchestrator</option>
                  <option value="3" style={{ background: '#1e293b', color: '#fff' }}>Doer</option>
                  <option value="4" style={{ background: '#1e293b', color: '#fff' }}>Etc</option>
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn primary"
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: '12.5px',
              fontWeight: '700',
              marginTop: '6px',
              justifyContent: 'center',
              borderRadius: '6px',
              letterSpacing: '0.3px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
              border: 'none',
              boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
              cursor: 'pointer'
            }}
          >
            {isLogin ? '로그인' : '가입하기'}
          </button>
        </div>

        <div style={{ textAlign: 'center', marginTop: '18px' }}>
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); setIsLogin(!isLogin); }}
            style={{
              color: '#38bdf8',
              textDecoration: 'none',
              fontSize: '12px',
              transition: 'color 0.15s ease'
            }}
            onMouseOver={e => e.currentTarget.style.color = '#7dd3fc'}
            onMouseOut={e => e.currentTarget.style.color = '#38bdf8'}
          >
            {isLogin ? '계정이 없으신가요? 회원가입' : '이미 계정이 있으신가요? 로그인'}
          </a>
        </div>
      </form>
    </div>
  );
}
