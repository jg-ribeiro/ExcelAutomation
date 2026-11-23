from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import Alert, AlertOut, Job

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status: Optional[str] = Query(None, description="Filtrar por status ('pending', 'auto_paused', 'resolved')"),
    db: Session = Depends(get_db)
):
    """Lista todos os alertas de sobreposição e conflito do sistema."""
    query = db.query(Alert, Job.name.label("job_name")).join(Job, Alert.job_id == Job.id)

    if status:
        query = query.filter(Alert.status == status)

    results = query.order_by(Alert.id.desc()).all()

    out = []
    for alert, job_name in results:
        out.append(
            AlertOut(
                id=alert.id,
                job_id=alert.job_id,
                job_name=job_name,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                details_json=alert.details_json,
                status=alert.status,
                consecutive_count=alert.consecutive_count,
                action_deadline=alert.action_deadline,
                created_at=alert.created_at,
                resolved_at=alert.resolved_at
            )
        )
    return out


@router.post("/{alert_id}/dismiss")
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """Descarta ou reconhece um alerta, concedendo novo prazo."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")

    alert.status = "acknowledged"
    db.commit()
    return {"success": True, "message": "Alerta reconhecido pelo usuário."}


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Marca manualmente um alerta como resolvido."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "Alerta marcado como resolvido."}
