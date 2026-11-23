from datetime import datetime
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import Job, JobCreate, JobUpdate, JobOut, Execution, Alert
from backend.app.engine.worker_queue import worker_queue
from backend.app.engine.conflict_detector import calculate_job_metrics, parse_interval_to_seconds, OVERLAP_SAFETY_THRESHOLD

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

# Referência para injeção do scheduler_service
scheduler_service_instance = None

def set_scheduler(sched):
    global scheduler_service_instance
    scheduler_service_instance = sched


@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    """Lista todos os jobs com métricas e status de conflito calculados."""
    jobs = db.query(Job).order_by(Job.id.asc()).all()
    out = []

    for j in jobs:
        metrics = calculate_job_metrics(db, j.id)
        avg_dur = metrics["avg_duration"]

        # Última execução
        last_exec = (
            db.query(Execution)
            .filter(Execution.job_id == j.id)
            .order_by(Execution.id.desc())
            .first()
        )

        # Próxima execução prevista no agendador
        next_run = None
        if scheduler_service_instance and j.is_active:
            next_run = scheduler_service_instance.get_next_run_time(j.id)

        # Alerta pendente de sobreposição
        pending_alert = (
            db.query(Alert)
            .filter(Alert.job_id == j.id, Alert.status.in_(["pending", "auto_paused"]))
            .first()
        )

        ratio = None
        has_conflict = False
        conflict_msg = None

        if j.schedule_type == "interval":
            interval_sec = parse_interval_to_seconds(j.schedule_value)
            if interval_sec and avg_dur:
                ratio = avg_dur / interval_sec
                if ratio >= OVERLAP_SAFETY_THRESHOLD or pending_alert:
                    has_conflict = True
                    conflict_msg = (
                        pending_alert.message if pending_alert
                        else f"Duração média ({avg_dur/60:.1f}m) ocupa {ratio*100:.0f}% do intervalo ({interval_sec/60:.1f}m)."
                    )
        elif pending_alert:
            has_conflict = True
            conflict_msg = pending_alert.message

        job_dict = {
            "id": j.id,
            "name": j.name,
            "file_path": j.file_path,
            "macro_name": j.macro_name,
            "schedule_type": j.schedule_type,
            "schedule_value": j.schedule_value,
            "is_active": j.is_active,
            "pause_reason": j.pause_reason,
            "query_timeout": j.query_timeout,
            "lock_timeout": j.lock_timeout,
            "created_at": j.created_at,
            "updated_at": j.updated_at,
            "avg_duration_seconds": avg_dur,
            "last_status": last_exec.status if last_exec else None,
            "last_run_at": last_exec.started_at if last_exec else None,
            "next_run_at": next_run,
            "has_conflict": has_conflict,
            "conflict_message": conflict_msg,
            "duration_ratio": ratio
        }
        out.append(JobOut(**job_dict))

    return out


@router.post("", response_model=JobOut)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Cadastra um novo arquivo de automação e registra no agendador."""
    existing = db.query(Job).filter(Job.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Já existe um job cadastrado com o nome '{payload.name}'.")

    new_job = Job(**payload.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    if scheduler_service_instance and new_job.is_active:
        scheduler_service_instance.sync_job(new_job.id, job=new_job)

    return JobOut.model_validate(new_job)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de um job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return JobOut.model_validate(job)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)):
    """Atualiza configurações de agendamento ou parâmetros de um job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    data = payload.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(job, field, val)

    # Se foi reativado manualmente, limpa o pause_reason
    if data.get("is_active") is True:
        job.pause_reason = None

    db.commit()
    db.refresh(job)

    if scheduler_service_instance:
        scheduler_service_instance.sync_job(job.id, job=job)

    return JobOut.model_validate(job)


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Remove um job e cancela seu agendamento."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    if scheduler_service_instance:
        scheduler_service_instance.pause_job(job.id)

    db.delete(job)
    db.commit()
    return {"success": True, "message": f"Job '{job.name}' excluído com sucesso."}


@router.post("/{job_id}/run")
def run_job_now(job_id: int, db: Session = Depends(get_db)):
    """Dispara a execução manual imediata de um job adicionando-o à fila."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    exec_id = worker_queue.enqueue_job(job.id, trigger_type="manual")
    return {
        "success": True,
        "message": f"Job '{job.name}' colocado na fila de execução com sucesso.",
        "execution_id": exec_id
    }


@router.post("/{job_id}/toggle-active")
def toggle_active(job_id: int, db: Session = Depends(get_db)):
    """Ativa ou pausa um job manualmente."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    job.is_active = not job.is_active
    if job.is_active:
        job.pause_reason = None
    else:
        job.pause_reason = "Pausado manualmente pelo usuário."

    db.commit()

    if scheduler_service_instance:
        scheduler_service_instance.sync_job(job.id, job=job)

    return {
        "success": True,
        "is_active": job.is_active,
        "message": f"Job '{job.name}' {'ativado' if job.is_active else 'pausado'} com sucesso."
    }
