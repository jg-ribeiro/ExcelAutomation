from datetime import datetime
import logging
import queue
import threading
import time
from typing import Dict, Any, Optional, List

from backend.app.core.database import SessionLocal
from backend.app.core.models import Job, Execution
from backend.app.engine.dynamic_runner import execute_job
from backend.app.engine.conflict_detector import ConflictDetector

logger = logging.getLogger("ExcelAutomation")


class WorkerQueue:
    """
    Fila de execução com bloqueio global (Concorrência Estrita = 1).
    Garante que nunca ocorram duas instâncias COM do Excel em simultâneo.
    """

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._current_job: Optional[Dict[str, Any]] = None
        self._scheduler_service: Optional[Any] = None

    def set_scheduler_service(self, scheduler):
        self._scheduler_service = scheduler

    def start(self):
        """Inicia a thread consumidora da fila."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="ExcelWorkerThread"
        )
        self._worker_thread.start()
        logger.info("[WORKER-QUEUE] Fila de execução única iniciada e aguardando jobs.")

    def stop(self):
        """Finaliza a thread da fila."""
        self._stop_event.set()
        # Envia sentinela para desbloquear get()
        self._queue.put(None)
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("[WORKER-QUEUE] Fila de execução encerrada.")

    def enqueue_job(self, job_id: int, trigger_type: str = "manual") -> Optional[int]:
        """
        Adiciona um job à fila de execução. Retorna o ID da Execution criada.
        """
        with SessionLocal() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"[WORKER-QUEUE] Tentativa de enfileirar job inexistente: ID {job_id}")
                return None

            job_name = job.name
            file_path = job.file_path
            macro_name = job.macro_name
            query_timeout = job.query_timeout
            lock_timeout = job.lock_timeout

            # Cria registro de execução em estado 'queued'
            execution = Execution(
                job_id=job.id,
                status="queued",
                trigger_type=trigger_type,
                started_at=None,
                finished_at=None
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            exec_id = execution.id

        logger.info(
            f"[WORKER-QUEUE] Job #{job_id} ('{job_name}') adicionado à fila "
            f"(Exec ID: {exec_id}, Disparo: {trigger_type})."
        )

        task_data = {
            "job_id": job_id,
            "job_name": job_name,
            "file_path": file_path,
            "macro_name": macro_name,
            "query_timeout": query_timeout,
            "lock_timeout": lock_timeout,
            "execution_id": exec_id,
            "trigger_type": trigger_type
        }
        self._queue.put(task_data)
        return exec_id

    def _worker_loop(self):
        """Loop principal da thread de execução única."""
        while not self._stop_event.is_set():
            try:
                task = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if task is None:  # Sentinela de parada
                break

            job_id = task["job_id"]
            exec_id = task["execution_id"]
            job_name = task["job_name"]

            with self._lock:
                self._current_job = {
                    "job_id": job_id,
                    "job_name": job_name,
                    "execution_id": exec_id,
                    "started_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Atualiza status no banco para 'running'
                with SessionLocal() as db:
                    execution = db.query(Execution).filter(Execution.id == exec_id).first()
                    if execution:
                        execution.status = "running"
                        execution.started_at = datetime.utcnow()
                        db.commit()

                # Executa o ciclo dinâmico do Excel
                result = execute_job(
                    job_id=job_id,
                    job_name=job_name,
                    file_path=task["file_path"],
                    macro_name=task["macro_name"],
                    query_timeout=task["query_timeout"],
                    lock_timeout=task["lock_timeout"]
                )

                # Persiste resultado da execução
                with SessionLocal() as db:
                    execution = db.query(Execution).filter(Execution.id == exec_id).first()
                    if execution:
                        execution.status = result["status"]
                        execution.finished_at = datetime.utcnow()
                        execution.duration_seconds = result["duration"]
                        execution.excel_pid = result["pid"]
                        execution.error_message = result["error"]
                        execution.log_snippet = result["log_snippet"]
                        db.commit()

                    # Avalia sobreposição e política de auto-pause
                    try:
                        ConflictDetector.evaluate_job(
                            db=db,
                            job_id=job_id,
                            scheduler_service=self._scheduler_service
                        )
                    except Exception as e:
                        logger.error(f"[WORKER-QUEUE] Erro no ConflictDetector após job #{job_id}: {e}", exc_info=True)

                self._current_job = None
                self._queue.task_done()

    def get_status(self) -> Dict[str, Any]:
        """Retorna o estado ao vivo da fila para a API e UI."""
        is_running = self._current_job is not None
        queue_snapshot = list(self._queue.queue)
        queued_items = [
            {"job_id": item["job_id"], "job_name": item["job_name"], "execution_id": item["execution_id"]}
            for item in queue_snapshot if item is not None
        ]

        return {
            "is_worker_running": is_running,
            "current_job": self._current_job,
            "queue_length": len(queued_items),
            "queued_jobs": queued_items
        }


# Instância singleton global do Worker
worker_queue = WorkerQueue()
