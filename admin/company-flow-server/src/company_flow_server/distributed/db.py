from __future__ import annotations
import os, uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, Boolean, DateTime, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg://crew:crew@localhost:5432/crew")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(engine,expire_on_commit=False)

class Base(DeclarativeBase): pass
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

def init_db():
    Base.metadata.create_all(engine)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            if "postgresql" in engine.url.drivername:
                conn.execute(text("ALTER TABLE run_history ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';"))
            elif "sqlite" in engine.url.drivername:
                conn.execute(text("ALTER TABLE run_history ADD COLUMN metadata_json JSON;"))
            conn.commit()
    except Exception:
        pass


class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    actor:Mapped[str]=mapped_column(String(255),index=True)
    action:Mapped[str]=mapped_column(String(128),index=True)
    resource:Mapped[str]=mapped_column(String(512),index=True)
    outcome:Mapped[str]=mapped_column(String(32),default="success")
    detail:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
