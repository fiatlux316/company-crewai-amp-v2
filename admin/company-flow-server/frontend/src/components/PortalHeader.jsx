import React, { useState, useRef, useEffect } from 'react';

const USER_TYPE_LABELS = {
  '1': 'Strategist (최고 관리자)',
  '2': 'Orchestrator (운영자)',
  '3': 'Doer (개발자/실무자)',
  '4': 'Etc (뷰어)'
};

export default function PortalHeader({
  services,
  currentServiceCode,
  onSelectService,
  onLogout,
  userTeamName,
  userName,
  userId,
  userType
}) {
  const [showProfile, setShowProfile] = useState(false);
  const popupRef = useRef(null);

  // 팝업 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(event) {
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        setShowProfile(false);
      }
    }
    if (showProfile) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfile]);

  return (
    <header className="portal-top-bar" style={{
      height: '52px',
      background: '#0f172a',
      borderBottom: '1px solid #1e293b',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      color: '#ffffff',
      flexShrink: 0,
      zIndex: 100
    }}>
      {/* 좌측: 포탈 로고 및 타이틀 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontWeight: '800',
          fontSize: '15px',
          letterSpacing: '-0.3px',
          background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          <span>🌐 AI Native Works</span>
        </div>

        <div style={{ width: '1px', height: '20px', background: '#334155' }}></div>

        {/* 중앙: 접근 가능한 서비스 상단 탭들 */}
        <nav style={{ display: 'flex', gap: '4px', overflowX: 'auto', alignItems: 'center' }}>
          {services.map(svc => {
            const isActive = svc.service_code === currentServiceCode;
            return (
              <button
                key={svc.id || svc.service_code}
                onClick={() => onSelectService(svc.service_code)}
                style={{
                  background: isActive ? '#1e293b' : 'transparent',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  border: isActive ? '1px solid #38bdf840' : '1px solid transparent',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: isActive ? '700' : '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap'
                }}
                onMouseOver={e => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#f1f5f9';
                    e.currentTarget.style.background = '#1e293b80';
                  }
                }}
                onMouseOut={e => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#94a3b8';
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <span>{svc.service_code === 'agentops' ? '🤖' : '🚀'}</span>
                <span>{svc.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* 우측: 사용자 정보 (클릭 시 상세 팝업), 소속 팀, 로그아웃 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '13px' }} ref={popupRef}>
        {userTeamName && (
          <span style={{
            background: 'rgba(56, 189, 248, 0.12)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            padding: '3px 10px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: '600'
          }}>
            🏢 {userTeamName}
          </span>
        )}

        {/* 사용자 이름 클릭 영역 & 드롭다운 팝업 */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowProfile(!showProfile)}
            style={{
              background: showProfile ? '#1e293b' : 'transparent',
              border: showProfile ? '1px solid #334155' : '1px solid transparent',
              color: '#f8fafc',
              cursor: 'pointer',
              padding: '5px 10px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
              transition: 'background 0.15s'
            }}
            title="사용자 정보 상세 보기"
          >
            <span>👤</span>
            <strong style={{ color: '#38bdf8' }}>{userName || 'User'}</strong>
            <span style={{ color: '#94a3b8' }}>님</span>
            <span style={{ fontSize: '10px', color: '#64748b', transform: showProfile ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
              ▼
            </span>
          </button>

          {/* 확장 상세정보 팝업 */}
          {showProfile && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              right: 0,
              width: '260px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '10px',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4)',
              padding: '16px',
              zIndex: 1000,
              animation: 'fadeIn 0.15s ease-out',
              color: '#f1f5f9'
            }}>
              <div style={{ borderBottom: '1px solid #334155', paddingBottom: '12px', marginBottom: '12px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>사용자 프로필</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc' }}>
                  {userName || 'User'}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>사번 (ID)</span>
                  <strong style={{ color: '#f8fafc' }}>{userId || '-'}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>소속 팀</span>
                  <strong style={{ color: '#38bdf8' }}>{userTeamName || '미지정'}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>사용자 유형</span>
                  <span style={{ color: '#a78bfa', fontWeight: '600' }}>
                    {USER_TYPE_LABELS[userType] || userType || 'Doer'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onLogout}
          className="btn secondary"
          style={{
            padding: '5px 12px',
            fontSize: '12px',
            background: '#1e293b',
            color: '#cbd5e1',
            border: '1px solid #334155',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          로그아웃
        </button>
      </div>
    </header>
  );
}
