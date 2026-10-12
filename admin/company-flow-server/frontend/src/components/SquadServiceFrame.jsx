import React from 'react';

export default function SquadServiceFrame({ service, userTeamName }) {
  if (!service) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        서비스를 선택해주세요.
      </div>
    );
  }

  return (
    <div style={{ padding: '32px', height: '100%', overflowY: 'auto', background: '#f8fafc' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* 서비스 타이틀 카드 */}
        <div className="panel" style={{ background: '#ffffff', borderRadius: '12px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontSize: '28px' }}>🚀</span>
                <h1 style={{ margin: 0, fontSize: '24px', color: '#0f172a' }}>{service.name}</h1>
                <span style={{ background: '#e0e7ff', color: '#4338ca', padding: '3px 10px', borderRadius: '9999px', fontSize: '12px', fontWeight: 'bold' }}>
                  {service.service_code}
                </span>
              </div>
              <p style={{ margin: '0 0 12px 0', color: '#64748b', fontSize: '15px' }}>
                {service.description || '스쿼드 전용 AI 서비스 포탈입니다.'}
              </p>
              <div style={{ fontSize: '13px', color: '#475569' }}>
                <span>소속 팀: </span>
                <strong style={{ color: '#1d4ed8' }}>{userTeamName || '미지정'}</strong>
                <span style={{ marginLeft: '12px', color: '#10b981' }}>● 서비스 정상 가동 중</span>
              </div>
            </div>
          </div>
        </div>

        {/* 서비스 초기 대시보드 카드들 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          <div className="panel" style={{ background: '#ffffff', borderRadius: '10px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ marginTop: 0, fontSize: '16px', color: '#1e293b' }}>📊 서비스 현황</h3>
            <p style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.5 }}>
              본 서비스는 <strong>{service.name}</strong> 전용 독립 모듈입니다. 팀원들과 공유할 수 있는 AI 도구와 연계되어 있습니다.
            </p>
            <div style={{ marginTop: '16px', padding: '12px', background: '#f1f5f9', borderRadius: '6px', fontSize: '13px' }}>
              <div>상태: <span style={{ color: '#16a34a', fontWeight: 'bold' }}>Active</span></div>
              <div>인증 방식: SSO / Token 연동</div>
            </div>
          </div>

          <div className="panel" style={{ background: '#ffffff', borderRadius: '10px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ marginTop: 0, fontSize: '16px', color: '#1e293b' }}>⚡ 빠른 작업</h3>
            <p style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.5 }}>
              이 서비스에서 지원하는 전용 작업 및 프롬프트 플로우를 실행할 수 있습니다.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
              <button className="btn secondary" style={{ justifyContent: 'center', width: '100%' }}>
                🔍 작업 데이터 조회
              </button>
              <button className="btn secondary" style={{ justifyContent: 'center', width: '100%' }}>
                📝 신규 작업 요청
              </button>
            </div>
          </div>

          <div className="panel" style={{ background: '#ffffff', borderRadius: '10px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ marginTop: 0, fontSize: '16px', color: '#1e293b' }}>🔗 모듈 확장 및 연동</h3>
            <p style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.5 }}>
              추후 서비스 URL, 내부 대시보드 SPA 또는 iframe 프레임을 본 영역에 유연하게 마운트할 수 있습니다.
            </p>
            <div style={{ marginTop: '16px', fontSize: '12px', color: '#94a3b8' }}>
              엔드포인트: <code>/services/{service.service_code}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
