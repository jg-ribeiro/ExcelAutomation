from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import Execution, ExecutionOut, Job

router = APIRouter(prefix="/api/executions", tags=["Executions"])


@router.get("", response_model=List[ExecutionOut])
def list_executions(
    job_id: Optional[int] = Query(None, description="Filtrar por ID do Job"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lista o histórico de execuções com ordenação decrescente por data."""
    query = db.query(Execution, Job.name.label("job_name")).join(Job, Execution.job_id == Job.id)

    if job_id:
        query = query.filter(Execution.job_id == job_id)
    if status:
        query = query.filter(Execution.status == status)

    results = query.order_by(Execution.id.desc()).offset(offset).limit(limit).all()

    out = []
    for exec_record, job_name in results:
        out.append(
            ExecutionOut(
                id=exec_record.id,
                job_id=exec_record.job_id,
                job_name=job_name,
                status=exec_record.status,
                trigger_type=exec_record.trigger_type,
                started_at=exec_record.started_at,
                finished_at=exec_record.finished_at,
                duration_seconds=exec_record.duration_seconds,
                excel_pid=exec_record.excel_pid,
                error_message=exec_record.error_message,
                log_snippet=exec_record.log_snippet
            )
        )
    return out


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes e log de uma execução específica."""
    item = (
        db.query(Execution, Job.name.label("job_name"))
        .join(Job, Execution.job_id == Job.id)
        .filter(Execution.id == execution_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Execução não encontrada.")

    exec_record, job_name = item
    return ExecutionOut(
        id=exec_record.id,
        job_id=exec_record.job_id,
        job_name=job_name,
        status=exec_record.status,
        trigger_type=exec_record.trigger_type,
        started_at=exec_record.started_at,
        finished_at=exec_record.finished_at,
        duration_seconds=exec_record.duration_seconds,
        excel_pid=exec_record.excel_pid,
        error_message=exec_record.error_message,
        log_snippet=exec_record.log_snippet
    )
