from datetime import datetime, timedelta
import logging
import re
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.core.config import (
    OVERLAP_SAFETY_THRESHOLD,
    MIN_RUNS_FOR_CONFLICT_CHECK,
    CONSECUTIVE_OVERLAPS_TO_AUTO_PAUSE,
    AUTO_PAUSE_DEADLINE_HOURS,
)
from backend.app.core.models import Job, Execution, Alert

logger = logging.getLogger("ExcelAutomation")


def parse_interval_to_seconds(value: str) -> Optional[int]:
    """
    Converte strings de intervalo como '10m', '30m', '1h', '2h', '45 min' em segundos.
    """
    if not value:
        return None
    val = value.strip().lower()
    
    # Horas: '1h', '2h', '1.5h'
    match_h = re.match(r"^([\d\.]+)\s*(?:h|hora|horas|hr|hrs)$", val)
    if match_h:
        return int(float(match_h.group(1)) * 3600)

    # Minutos: '10m', '10min', '10'
    match_m = re.match(r"^([\d\.]+)\s*(?:m|min|minuto|minutos)?$", val)
    if match_m:
        return int(float(match_m.group(1)) * 60)

    # Segundos: '120s'
    match_s = re.match(r"^([\d\.]+)\s*(?:s|sec|segundos)$", val)
    if match_s:
        return int(float(match_s.group(1)))

    return None


def calculate_job_metrics(db: Session, job_id: int, sample_size: int = 5) -> Dict[str, Any]:
    """
    Calcula a média móvel de duração e última execução com base nas últimas execuções.
    """
    executions = (
        db.query(Execution)
        .filter(Execution.job_id == job_id, Execution.duration_seconds.isnot(None))
        .order_by(Execution.id.desc())
        .limit(sample_size)
        .all()
    )

    if not executions:
        return {
            "sample_count": 0,
            "avg_duration": None,
            "max_duration": None,
            "last_duration": None
        }

    durations = [e.duration_seconds for e in executions if e.duration_seconds is not None]
    return {
        "sample_count": len(durations),
        "avg_duration": sum(durations) / len(durations) if durations else None,
        "max_duration": max(durations) if durations else None,
        "last_duration": durations[0] if durations else None
    }


class ConflictDetector:
    """
    Motor de detecção de sobreposição e política de auto-pause.
    """

    @classmethod
    def evaluate_job(
        cls,
        db: Session,
        job_id: int,
        scheduler_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Avalia se as execuções recentes de um job indicam risco de sobreposição com sua frequência.
        Executa auto-pause caso as violações ultrapassem o limite de tolerância.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.is_active:
            return {"status": "skipped", "reason": "Job inativo ou inexistente"}

        metrics = calculate_job_metrics(db, job_id)
        avg_dur = metrics["avg_duration"]
        count = metrics["sample_count"]

        # Requer amostragem mínima de execuções
        if count < MIN_RUNS_FOR_CONFLICT_CHECK or avg_dur is None:
            return {
                "status": "insufficient_data",
                "sample_count": count,
                "required": MIN_RUNS_FOR_CONFLICT_CHECK
            }

        # Avaliação de Jobs com agendamento por Intervalo (ex: a cada 10 minutos)
        if job.schedule_type == "interval":
            interval_sec = parse_interval_to_seconds(job.schedule_value)
            if not interval_sec or interval_sec <= 0:
                return {"status": "invalid_interval"}

            ratio = avg_dur / interval_sec
            avg_min = avg_dur / 60
            int_min = interval_sec / 60

            # Caso 1: Risco ou Colisão Crítica Detectada
            if ratio >= OVERLAP_SAFETY_THRESHOLD:
                severity = "critical" if avg_dur >= interval_sec else "warning"
                title = f"Risco de Sobreposição: {job.name}"
                msg = (
                    f"O job '{job.name}' tem duração média de {avg_min:.1f} min, mas está "
                    f"agendado a cada {int_min:.1f} min (Ocupação: {ratio*100:.0f}%). "
                    f"Isso causará acúmulo e saturação na fila."
                )

                # Busca se já existe alerta pendente para este job
                active_alert = (
                    db.query(Alert)
                    .filter(
                        Alert.job_id == job_id,
                        Alert.alert_type == "overlap_risk",
                        Alert.status == "pending"
                    )
                    .first()
                )

                now = datetime.utcnow()
                if not active_alert:
                    # Cria novo alerta de aviso
                    deadline = now + timedelta(hours=AUTO_PAUSE_DEADLINE_HOURS)
                    new_alert = Alert(
                        job_id=job_id,
                        alert_type="overlap_risk",
                        severity=severity,
                        title=title,
                        message=msg,
                        status="pending",
                        consecutive_count=1,
                        action_deadline=deadline,
                        created_at=now
                    )
                    db.add(new_alert)
                    db.commit()
                    logger.warning(f"[CONFLICT-DETECTOR] Alerta gerado para '{job.name}': {msg}")
                    return {
                        "status": "alert_created",
                        "severity": severity,
                        "ratio": ratio,
                        "consecutive_count": 1
                    }

                # Se o alerta já existia, atualiza contagem e verifica auto-pause
                active_alert.consecutive_count += 1
                active_alert.message = msg
                active_alert.severity = severity

                should_auto_pause = (
                    active_alert.consecutive_count >= CONSECUTIVE_OVERLAPS_TO_AUTO_PAUSE
                    or (active_alert.action_deadline and now >= active_alert.action_deadline)
                )

                if should_auto_pause:
                    # Aciona AUTO-PAUSE!
                    job.is_active = False
                    pause_msg = (
                        f"Pausado automaticamente pelo sistema: duração média de {avg_min:.1f}m "
                        f"ultrapassa o intervalo agendado de {int_min:.1f}m após "
                        f"{active_alert.consecutive_count} execuções consecutivas em sobreposição."
                    )
                    job.pause_reason = pause_msg
                    active_alert.status = "auto_paused"
                    db.commit()

                    logger.critical(
                        f"[CONFLICT-DETECTOR] AUTO-PAUSE ACIONADO para Job #{job.id} ('{job.name}')! {pause_msg}"
                    )

                    if scheduler_service:
                        try:
                            scheduler_service.pause_job(job.id)
                        except Exception as e:
                            logger.error(f"[CONFLICT-DETECTOR] Erro ao desregistrar job do agendador: {e}")

                    return {
                        "status": "auto_paused",
                        "reason": pause_msg,
                        "consecutive_count": active_alert.consecutive_count
                    }

                db.commit()
                return {
                    "status": "alert_updated",
                    "consecutive_count": active_alert.consecutive_count,
                    "ratio": ratio
                }

            # Caso 2: Margem Saudável (ratio < threshold)
            else:
                # Se existia alerta pendente anterior, agora está resolvido
                pending_alerts = (
                    db.query(Alert)
                    .filter(
                        Alert.job_id == job_id,
                        Alert.alert_type == "overlap_risk",
                        Alert.status == "pending"
                    )
                    .all()
                )
                if pending_alerts:
                    for a in pending_alerts:
                        a.status = "resolved"
                        a.resolved_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"[CONFLICT-DETECTOR] Alerta(s) de sobreposição resolvido(s) para '{job.name}'.")

                return {"status": "healthy", "ratio": ratio}

        return {"status": "not_applicable"}
