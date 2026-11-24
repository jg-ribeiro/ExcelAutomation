from datetime import datetime
import logging
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.core.database import SessionLocal
from backend.app.core.models import Job
from backend.app.engine.conflict_detector import parse_interval_to_seconds

logger = logging.getLogger("ExcelAutomation")


class SchedulerService:
    """
    Gerenciador central do APScheduler para agendamentos de jobs.
    Despacha gatilhos diretamente para a fila serializada (worker_queue).
    """

    def __init__(self, worker_queue):
        self.worker_queue = worker_queue
        self.scheduler = BackgroundScheduler(daemon=True)
        self._is_started = False

    def start(self):
        """Inicia o agendador e registra todos os jobs ativos."""
        if not self._is_started:
            self.scheduler.start()
            self._is_started = True
            logger.info("[SCHEDULER] APScheduler iniciado com sucesso.")
            self.resync_all_jobs()

    def shutdown(self):
        """Encerra o agendador gracioso."""
        if self._is_started:
            self.scheduler.shutdown(wait=False)
            self._is_started = False
            logger.info("[SCHEDULER] APScheduler encerrado.")

    def resync_all_jobs(self):
        """Sincroniza todos os jobs ativos do banco com o agendador."""
        with SessionLocal() as db:
            jobs = db.query(Job).all()
            for job in jobs:
                self.sync_job(job.id, job=job)

    def sync_job(self, job_id: int, job: Optional[Job] = None):
        """Adiciona, atualiza ou remove um job do agendador."""
        job_tag = f"job_{job_id}"

        # Remove gatilho anterior caso exista
        if self.scheduler.get_job(job_tag):
            self.scheduler.remove_job(job_tag)

        if not job:
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_id).first()

        if not job or not job.is_active:
            logger.info(f"[SCHEDULER] Job #{job_id} está inativo ou inexistente. Não agendado.")
            return

        job_name = job.name
        job_id_val = job.id

        def _trigger_action():
            logger.info(f"[SCHEDULER] Gatilho disparado para Job #{job_id_val} ('{job_name}')!")
            self.worker_queue.enqueue_job(job_id_val, trigger_type="schedule")

        try:
            if job.schedule_type == "daily":
                # Formato esperado: "HH:MM" (ex: "03:00")
                parts = job.schedule_value.strip().split(":")
                hour = int(parts[0]) if len(parts) > 0 else 3
                minute = int(parts[1]) if len(parts) > 1 else 0
                trigger = CronTrigger(hour=hour, minute=minute)
                self.scheduler.add_job(_trigger_action, trigger=trigger, id=job_tag, name=job.name)
                logger.info(f"[SCHEDULER] Job #{job.id} ('{job.name}') agendado diariamente às {hour:02d}:{minute:02d}.")

            elif job.schedule_type == "interval":
                seconds = parse_interval_to_seconds(job.schedule_value)
                if not seconds or seconds < 30:
                    logger.error(f"[SCHEDULER] Intervalo inválido ou muito curto para Job #{job.id}: '{job.schedule_value}'")
                    return
                trigger = IntervalTrigger(seconds=seconds)
                self.scheduler.add_job(_trigger_action, trigger=trigger, id=job_tag, name=job.name)
                logger.info(f"[SCHEDULER] Job #{job.id} ('{job.name}') agendado a cada {seconds}s ({job.schedule_value}).")

        except Exception as e:
            logger.error(f"[SCHEDULER] Falha ao configurar agendamento do Job #{job.id}: {e}", exc_info=True)

    def pause_job(self, job_id: int):
        """Pausa o agendamento de um job."""
        job_tag = f"job_{job_id}"
        if self.scheduler.get_job(job_tag):
            self.scheduler.remove_job(job_tag)
            logger.info(f"[SCHEDULER] Job #{job_id} removido do agendador ativo.")

    def get_next_run_time(self, job_id: int) -> Optional[datetime]:
        """Retorna o timestamp da próxima execução agendada."""
        job_tag = f"job_{job_id}"
        sched_job = self.scheduler.get_job(job_tag)
        if sched_job and sched_job.next_run_time:
            return sched_job.next_run_time
        return None
