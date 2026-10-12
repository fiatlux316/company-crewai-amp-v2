import React, { useState, useEffect } from 'react';
import PortalHeader from './components/PortalHeader';
import SquadServiceFrame from './components/SquadServiceFrame';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import GeneratePersona from './components/GeneratePersona';
import GenerateCrew from './components/GenerateCrew';
import CrewProcess from './components/CrewProcess';
import ExecutionHistory from './components/ExecutionHistory';
import NodeFlowDesigner from './components/NodeFlowDesigner';
import McpCatalog from './components/McpCatalog';
import UserManagement from './components/UserManagement';
import ServiceAccessManagement from './components/ServiceAccessManagement';
import Auth from './components/Auth';
import RAGChatbot from './components/RAGChatbot';
import DialogContainer from './components/Dialog';
import { api } from './utils/api';
import './index.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('persona');
  const [initialRunId, setInitialRunId] = useState(null);
  const [initialCrewId, setInitialCrewId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Portal Multi-Service State
  const [accessibleServices, setAccessibleServices] = useState([]);
  const [currentServiceCode, setCurrentServiceCode] = useState(null);
  const [servicesLoaded, setServicesLoaded] = useState(false);

  const isAgentOps = (code) => code === 'agentops';

  const loadUserServices = () => {
    api.fetchMyServices()
      .then(services => {
        const list = Array.isArray(services) ? services : [];
        setAccessibleServices(list);
        setServicesLoaded(true);
        if (list.length > 0) {
          setCurrentServiceCode(prev => {
            if (prev && list.some(s => s.service_code === prev)) {
              return prev;
            }
            const agentOpsSvc = list.find(s => isAgentOps(s.service_code));
            return agentOpsSvc ? agentOpsSvc.service_code : list[0].service_code;
          });
        } else {
          setCurrentServiceCode(null);
        }
      })
      .catch(err => {
        console.error("Failed to load user services:", err);
        setAccessibleServices([]);
        setServicesLoaded(true);
        setCurrentServiceCode(null);
      });
  };

  useEffect(() => {
    if (localStorage.getItem('access_token')) {
      setIsAuthenticated(true);
      loadUserServices();
    }
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    loadUserServices();
  };

  const handleNavigateHistory = (runId) => {
    if (runId) setInitialRunId(runId);
    setActiveTab('history');
  };

  const handleNavigateCrew = (crewId) => {
    if (crewId) setInitialCrewId(crewId);
    setActiveTab('crew');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user_name');
    localStorage.removeItem('team_id');
    localStorage.removeItem('team_name');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="app-layout">
        <Auth onLogin={handleLoginSuccess} />
        <DialogContainer />
      </div>
    );
  }

  const userType = localStorage.getItem('user_type');
  const userId = localStorage.getItem('user_id');
  const userName = localStorage.getItem('user_name');
  const teamName = localStorage.getItem('team_name');

  const activeServiceObj = accessibleServices.find(s => s.service_code === currentServiceCode) || {
    service_code: currentServiceCode,
    name: currentServiceCode
  };

  return (
    <div className="portal-container">
      {/* Tier 1: 상단 포탈 헤더 (내 팀이 접근 가능한 서비스 탭 목록 노출) */}
      <PortalHeader
        services={accessibleServices}
        currentServiceCode={currentServiceCode}
        onSelectService={(code) => setCurrentServiceCode(code)}
        onLogout={handleLogout}
        userTeamName={teamName}
        userName={userName}
        userId={userId}
        userType={userType}
      />

      {/* Tier 2: 하단 서비스 뷰 프레임 */}
      <div className="portal-body">
        {accessibleServices.length === 0 ? (
          <div style={{
            flex: 1,
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#090d16',
            color: '#94a3b8',
            textAlign: 'center',
            padding: '40px'
          }}>
            <div style={{ fontSize: '56px', marginBottom: '16px' }}>🔒</div>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#f1f5f9', marginBottom: '10px' }}>
              접근 가능한 서비스가 없습니다
            </h3>
            <p style={{ fontSize: '14px', maxWidth: '440px', lineHeight: '1.6', color: '#94a3b8', margin: 0 }}>
              소속 팀(<strong>{teamName || '미지정'}</strong>)에 할당된 포탈 서비스 권한이 없습니다.<br />
              관리자(이마트CX팀)에게 서비스 접근 권한을 요청해주세요.
            </p>
          </div>
        ) : isAgentOps(currentServiceCode) ? (
          /* 기존 AgentOps 메인 환경 (사이드바 + 메인 작업공간) */
          <div className="app-layout">
            <Sidebar 
              activeTab={activeTab} 
              setActiveTab={setActiveTab} 
              collapsed={sidebarCollapsed} 
              onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
              userType={userType}
              teamName={teamName}
            />
            <div className="main-wrapper">
              <Header activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} />
              <div className="main-content">
                {activeTab === 'persona' && <GeneratePersona onKickoff={handleNavigateHistory} />}
                {activeTab === 'generate_crew' && <GenerateCrew onNavigateCrew={handleNavigateCrew} />}
                {activeTab === 'crew' && <CrewProcess onNavigateHistory={handleNavigateHistory} initialCrewId={initialCrewId} userType={userType} userId={userId} />}
                {activeTab === 'history' && <ExecutionHistory initialRunId={initialRunId} onNavigateCrew={handleNavigateCrew} userType={userType} userId={userId} />}
                {activeTab === 'flow' && <NodeFlowDesigner />}
                {activeTab === 'mcp' && <McpCatalog />}
                {activeTab === 'service_access' && <ServiceAccessManagement />}
                {activeTab === 'users' && <UserManagement />}
                {activeTab === 'rag' && <RAGChatbot />}
                {activeTab === 'swagger' && (
                  <iframe
                    src="/docs"
                    style={{ width: '100%', height: '100%', border: 'none' }}
                    title="Swagger API"
                  />
                )}
              </div>
            </div>
          </div>
        ) : (
          /* squad1 ~ squad6 등 개별 신규 서비스 전용 초기화면 프레임 */
          <div style={{ flex: 1, width: '100%', height: '100%', overflow: 'hidden' }}>
            <SquadServiceFrame service={activeServiceObj} userTeamName={teamName} />
          </div>
        )}
      </div>

      <DialogContainer />
    </div>
  );
}

export default App;
