import unittest
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.models import Base, Job, Execution, Alert
from backend.app.engine.conflict_detector import (
    parse_interval_to_seconds,
    calculate_job_metrics,
    ConflictDetector
)
from backend.app.engine.worker_queue import WorkerQueue
from backend.app.main import app


class TestFullSystemSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_api_system_status(self):
        """Verifica se o endpoint /api/system/status responde com integridade."""
        response = self.client.get("/api/system/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_worker_running", data)
        self.assertIn("total_jobs", data)
        self.assertIn("active_jobs", data)
        self.assertIn("server_time", data)

    def test_02_job_crud_lifecycle(self):
        """Testa o ciclo de vida completo de cadastro, listagem, atualização e exclusão de um job."""
        job_payload = {
            "name": f"Teste API Job {int(time.time()*1000)}",
            "file_path": r"\\server\share\planilha.xlsm",
            "macro_name": "SalvarDados",
            "schedule_type": "interval",
            "schedule_value": "30m",
            "is_active": True,
            "query_timeout": 300,
            "lock_timeout": 120
        }

        # Criação
        res_create = self.client.post("/api/jobs", json=job_payload)
        self.assertEqual(res_create.status_code, 200)
        created_job = res_create.json()
        job_id = created_job["id"]
        self.assertEqual(created_job["name"], job_payload["name"])

        # Leitura
        res_get = self.client.get(f"/api/jobs/{job_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["file_path"], job_payload["file_path"])

        # Atualização
        res_update = self.client.put(f"/api/jobs/{job_id}", json={"schedule_value": "1h"})
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["schedule_value"], "1h")

        # Toggle Active
        res_toggle = self.client.post(f"/api/jobs/{job_id}/toggle-active")
        self.assertEqual(res_toggle.status_code, 200)
        self.assertFalse(res_toggle.json()["is_active"])

        # Exclusão
        res_del = self.client.delete(f"/api/jobs/{job_id}")
        self.assertEqual(res_del.status_code, 200)

        # Confirma que não existe mais
        res_get_deleted = self.client.get(f"/api/jobs/{job_id}")
        self.assertEqual(res_get_deleted.status_code, 404)

    def test_03_conflict_detector_mathematics_and_auto_pause(self):
        """Valida que uma rotina que dura 20 min com atualização a cada 10 min gera alerta e auto-pause."""
        job = Job(
            name=f"Job Moagem Rapida {int(time.time()*1000)}",
            file_path=r"\\server\cpc\moagem.xlsm",
            macro_name="SalvarTodos",
            schedule_type="interval",
            schedule_value="10m",  # Intervalo de 10 min (600s)
            is_active=True
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Simula execuções com duração de 20 minutos (1200s)
        for _ in range(3):
            now = datetime.now()
            exec_rec = Execution(
                job_id=job.id,
                status="success",
                started_at=now - timedelta(minutes=20),
                finished_at=now,
                duration_seconds=1200.0
            )
            self.db.add(exec_rec)
        self.db.commit()

        # Ciclo 1: Risco detectado, cria alerta pendente
        res1 = ConflictDetector.evaluate_job(self.db, job.id)
        self.assertEqual(res1["status"], "alert_created")
        self.assertEqual(res1["severity"], "critical")
        self.assertEqual(res1["consecutive_count"], 1)

        # Ciclo 2: Atualiza alerta
        res2 = ConflictDetector.evaluate_job(self.db, job.id)
        self.assertEqual(res2["status"], "alert_updated")
        self.assertEqual(res2["consecutive_count"], 2)

        # Ciclo 3: Auto-pause acionado!
        res3 = ConflictDetector.evaluate_job(self.db, job.id)
        self.assertEqual(res3["status"], "auto_paused")

        # Verifica se o job foi pausado sem ser excluído
        self.db.refresh(job)
        self.assertFalse(job.is_active)
        self.assertIn("Pausado automaticamente pelo sistema", job.pause_reason)

    def test_04_logs_endpoint(self):
        """Testa recuperação de logs em memória via API."""
        res = self.client.get("/api/logs?limit=50")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("logs", data)
        self.assertIsInstance(data["logs"], list)

    def test_05_frontend_static_build_exists(self):
        """Garante que os arquivos do frontend foram compilados para distribuição."""
        dist_dir = ROOT_DIR / "frontend" / "dist"
        self.assertTrue(dist_dir.exists())
        self.assertTrue((dist_dir / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
