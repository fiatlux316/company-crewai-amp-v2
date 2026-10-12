from __future__ import annotations
import os, uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, Boolean, DateTime, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg://crew:crew@localhost:5432/crew")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(engine,expire_on_commit=False)

class Base(DeclarativeBase): pass

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PortalService(Base):
    __tablename__ = "portal_services"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_num: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ServiceTeamAccess(Base):
    __tablename__ = "service_team_access"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[str] = mapped_column(String(36), index=True)
    team_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("service_id", "team_id", name="uq_service_team_access"),)

class User(Base):
    __tablename__="users"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id:Mapped[str]=mapped_column(String(6),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(255))
    password:Mapped[str]=mapped_column(String(64))
    user_type:Mapped[str]=mapped_column(String(1))
    status:Mapped[str]=mapped_column(String(1),default="0")
    team_id:Mapped[str | None]=mapped_column(String(36),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))

class CrewSetting(Base):
    __tablename__="crew_settings"
    crew_id:Mapped[str]=mapped_column(String(255),primary_key=True)
    schedule_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    schedule_cron:Mapped[str]=mapped_column(String(128),default="")
    default_inputs:Mapped[dict]=mapped_column(JSON,default=dict)
    metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
class RunHistory(Base):
    __tablename__="run_history"
    run_id:Mapped[str]=mapped_column(String(64),primary_key=True,default=lambda:str(uuid.uuid4()))
    crew_id:Mapped[str]=mapped_column(String(255),index=True)
    version:Mapped[str]=mapped_column(String(64))
    trigger:Mapped[str]=mapped_column(String(32),default="manual")
    status:Mapped[str]=mapped_column(String(32),index=True)
    inputs:Mapped[dict]=mapped_column(JSON,default=dict)
    outputs:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    error:Mapped[str|None]=mapped_column(Text,nullable=True)
    verbose:Mapped[list]=mapped_column(JSON,default=list)
    metadata_json:Mapped[dict|None]=mapped_column(JSON,nullable=True,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    ended_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class ScheduleClaim(Base):
    __tablename__="schedule_claims"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    crew_id:Mapped[str]=mapped_column(String(255))
    minute_key:Mapped[str]=mapped_column(String(32))
    __table_args__=(UniqueConstraint("crew_id","minute_key",name="uq_schedule_claim"),)

DEFAULT_TEAMS = [
    "이마트팀",
    "이마트SAP1팀",
    "이마트SAP2팀",
    "이마트POS팀",
    "이마트CX팀",
    "이마트앱서비스팀",
    "이마트24팀",
    "이마트24POS팀",
    "건설팀",
    "프라퍼티팀"
]

DEFAULT_SERVICES = [
    {"service_code": "agent-platform", "name": "Agent Platform", "description": "Crew AI 및 Multi-Agent 운영 관리 플랫폼", "order_num": 1},
    {"service_code": "squad1", "name": "squad1", "description": "스쿼드 1 AI 서비스", "order_num": 2},
    {"service_code": "squad2", "name": "squad2", "description": "스쿼드 2 AI 서비스", "order_num": 3},
    {"service_code": "squad3", "name": "squad3", "description": "스쿼드 3 AI 서비스", "order_num": 4},
    {"service_code": "squad4", "name": "squad4", "description": "스쿼드 4 AI 서비스", "order_num": 5},
    {"service_code": "squad5", "name": "squad5", "description": "스쿼드 5 AI 서비스", "order_num": 6},
    {"service_code": "squad6", "name": "squad6", "description": "스쿼드 6 AI 서비스", "order_num": 7},
]

def init_db():
    Base.metadata.create_all(engine)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            if "postgresql" in engine.url.drivername:
                conn.execute(text("ALTER TABLE run_history ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id VARCHAR(36);"))
            elif "sqlite" in engine.url.drivername:
                try:
                    conn.execute(text("ALTER TABLE run_history ADD COLUMN metadata_json JSON;"))
                except Exception:
                    pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN team_id VARCHAR(36);"))
                except Exception:
                    pass
            conn.commit()
    except Exception:
        pass

    # 시딩(Seeding): 기본 팀 및 기본 서비스 등록 및 기본 접근 권한 매핑
    try:
        with SessionLocal() as db:
            # 1. Teams 시딩
            existing_teams = {t.name: t for t in db.query(Team).all()}
            for team_name in DEFAULT_TEAMS:
                if team_name not in existing_teams:
                    new_team = Team(name=team_name)
                    db.add(new_team)
            db.commit()

            # 갱신된 팀 맵
            all_teams = db.query(Team).all()
            team_map = {t.name: t for t in all_teams}

            # 2. Services 시딩
            existing_services = {s.service_code: s for s in db.query(PortalService).all()}
            for svc_info in DEFAULT_SERVICES:
                code = svc_info["service_code"]
                if code not in existing_services:
                    new_svc = PortalService(
                        service_code=code,
                        name=svc_info["name"],
                        description=svc_info["description"],
                        order_num=svc_info["order_num"],
                        is_active=True
                    )
                    db.add(new_svc)
            db.commit()

            # 3. Agent Platform 기본 매핑: 모든 팀에 Agent Platform 기본 접근 권한 부여
            agent_platform_svc = db.query(PortalService).filter(PortalService.service_code == "agent-platform").first()
            if agent_platform_svc:
                for team in all_teams:
                    exists = db.query(ServiceTeamAccess).filter(
                        ServiceTeamAccess.service_id == agent_platform_svc.id,
                        ServiceTeamAccess.team_id == team.id
                    ).first()
                    if not exists:
                        db.add(ServiceTeamAccess(service_id=agent_platform_svc.id, team_id=team.id))
                db.commit()
    except Exception as e:
        print(f"Error during seeding: {e}")


class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    actor:Mapped[str]=mapped_column(String(255),index=True)
    action:Mapped[str]=mapped_column(String(128),index=True)
    resource:Mapped[str]=mapped_column(String(512),index=True)
    outcome:Mapped[str]=mapped_column(String(32),default="success")
    detail:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
