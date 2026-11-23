from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import SystemStatusOut, Job, Alert, Execution, ExecutionOut
from backend.app.engine.worker_queue import worker_queue

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/status", response_model=SystemStatusOut)
def get_system_status(db: Session = Depends(get_db)):
    """Retorna os indicadores vitais do sistema: fila, jobs ativos e alertas."""
    queue_status = worker_queue.get_status()

    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.is_active == True).count()
    pending_alerts = db.query(Alert).filter(Alert.status.in_(["pending", "auto_paused"])).count()

    last_exec_record = (
        db.query(Execution, Job.name.label("job_name"))
        .join(Job, Execution.job_id == Job.id)
        .order_by(Execution.id.desc())
        .first()
    )

    last_exec_out = None
    if last_exec_record:
        exec_item, j_name = last_exec_record
        last_exec_out = ExecutionOut(
            id=exec_item.id,
            job_id=exec_item.job_id,
            job_name=j_name,
            status=exec_item.status,
            trigger_type=exec_item.trigger_type,
            started_at=exec_item.started_at,
            finished_at=exec_item.finished_at,
            duration_seconds=exec_item.duration_seconds,
            excel_pid=exec_item.excel_pid,
            error_message=exec_item.error_message,
            log_snippet=None
        )

    return SystemStatusOut(
        is_worker_running=queue_status["is_worker_running"],
        current_job=queue_status["current_job"],
        queue_length=queue_status["queue_length"],
        queued_jobs=queue_status["queued_jobs"],
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        pending_alerts=pending_alerts,
        last_execution=last_exec_out,
        server_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
