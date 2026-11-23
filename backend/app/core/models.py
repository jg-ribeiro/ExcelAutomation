from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field

Base = declarative_base()


# ==========================================
# MODELOS ORM (SQLAlchemy)
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(150), nullable=True)
    role = Column(String(50), nullable=False, default="OPERATOR")  # 'ADMIN' ou 'OPERATOR'
    is_active = Column(Boolean, default=True, index=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    file_path = Column(String(500), nullable=False)
    macro_name = Column(String(100), nullable=True, default="SalvarTodos")
    schedule_type = Column(String(50), nullable=False, default="daily")  # 'daily', 'interval', 'manual'
    schedule_value = Column(String(100), nullable=False, default="03:00")  # '03:00' ou '10m', '30m', '1h'
    is_active = Column(Boolean, default=True, index=True)
    pause_reason = Column(String(300), nullable=True)
    query_timeout = Column(Integer, default=300)
    lock_timeout = Column(Integer, default=120)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    executions = relationship("Execution", back_populates="job", cascade="all, delete-orphan", order_by="desc(Execution.id)")
    alerts = relationship("Alert", back_populates="job", cascade="all, delete-orphan", order_by="desc(Alert.id)")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="queued")  # queued, running, success, failed, timeout, lock_timeout, aborted
    trigger_type = Column(String(50), nullable=False, default="schedule")  # schedule, manual, retry
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    excel_pid = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    log_snippet = Column(Text, nullable=True)

    job = relationship("Job", back_populates="executions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # overlap_risk, timeout_exceeded, consecutive_errors
    severity = Column(String(50), nullable=False, default="warning")  # warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, acknowledged, auto_paused, resolved
    consecutive_count = Column(Integer, default=1)
    action_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    job = relationship("Job", back_populates="alerts")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)
    description = Column(String(250), nullable=True)


# ==========================================
# SCHEMAS PYDANTIC (API DTOs)
# ==========================================

class UserLogin(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    role: str
    is_active: bool
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class JobCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    file_path: str = Field(..., min_length=3, max_length=500)
    macro_name: Optional[str] = "SalvarTodos"
    schedule_type: str = Field("daily", pattern="^(daily|interval|manual)$")
    schedule_value: str = Field("03:00")
    is_active: bool = True
    query_timeout: int = Field(300, ge=30, le=3600)
    lock_timeout: int = Field(120, ge=10, le=1800)


class JobUpdate(BaseModel):
    name: Optional[str] = None
    file_path: Optional[str] = None
    macro_name: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    is_active: Optional[bool] = None
    pause_reason: Optional[str] = None
    query_timeout: Optional[int] = None
    lock_timeout: Optional[int] = None


class JobOut(BaseModel):
    id: int
    name: str
    file_path: str
    macro_name: Optional[str]
    schedule_type: str
    schedule_value: str
    is_active: bool
    pause_reason: Optional[str]
    query_timeout: int
    lock_timeout: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Métricas calculadas para a UI
    avg_duration_seconds: Optional[float] = None
    last_status: Optional[str] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    has_conflict: bool = False
    conflict_message: Optional[str] = None
    duration_ratio: Optional[float] = None

    class Config:
        from_attributes = True


class ExecutionOut(BaseModel):
    id: int
    job_id: int
    job_name: Optional[str] = None
    status: str
    trigger_type: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    excel_pid: Optional[int]
    error_message: Optional[str]
    log_snippet: Optional[str]

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    job_id: int
    job_name: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    message: str
    details_json: Optional[str]
    status: str
    consecutive_count: int
    action_deadline: Optional[datetime]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class SystemStatusOut(BaseModel):
    is_worker_running: bool
    current_job: Optional[dict] = None
    queue_length: int
    queued_jobs: List[dict] = []
    total_jobs: int
    active_jobs: int
    pending_alerts: int
    last_execution: Optional[ExecutionOut] = None
    server_time: str
