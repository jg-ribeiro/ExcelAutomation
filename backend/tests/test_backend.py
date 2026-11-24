import unittest
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.database import SessionLocal, init_db, engine
from backend.app.core.models import Base, Job, Execution, Alert
from backend.app.engine.conflict_detector import (
    parse_interval_to_seconds,
    calculate_job_metrics,
    ConflictDetector
)


class TestConflictDetector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_parse_interval_to_seconds(self):
        self.assertEqual(parse_interval_to_seconds("10m"), 600)
        self.assertEqual(parse_interval_to_seconds("10 min"), 600)
        self.assertEqual(parse_interval_to_seconds("1h"), 3600)
        self.assertEqual(parse_interval_to_seconds("2h"), 7200)
        self.assertEqual(parse_interval_to_seconds("30m"), 1800)
        self.assertEqual(parse_interval_to_seconds("90s"), 90)

    def test_overlap_detection_and_auto_pause(self):
        # Cria job de teste com intervalo de 10 minutos (600s)
        test_job = Job(
            name=f"Job Teste Conflito {int(time.time()*1000)}",
            file_path=r"C:\fake\test.xlsm",
            macro_name="TestMacro",
            schedule_type="interval",
            schedule_value="10m",
            is_active=True
        )
        self.db.add(test_job)
        self.db.commit()
        self.db.refresh(test_job)

        # Simula execuções com duração de 15 minutos (900s), que excede os 600s do intervalo!
        for _ in range(3):
            exec_rec = Execution(
                job_id=test_job.id,
                status="success",
                started_at=datetime.utcnow() - timedelta(minutes=15),
                finished_at=datetime.utcnow(),
                duration_seconds=900.0
            )
            self.db.add(exec_rec)
        self.db.commit()

        # Ciclo 1: Deve criar alerta pendente (consecutive_count = 1)
        res1 = ConflictDetector.evaluate_job(self.db, test_job.id)
        self.assertEqual(res1["status"], "alert_created")
        self.assertEqual(res1["consecutive_count"], 1)

        # Ciclo 2: Deve atualizar alerta (consecutive_count = 2)
        res2 = ConflictDetector.evaluate_job(self.db, test_job.id)
        self.assertEqual(res2["status"], "alert_updated")
        self.assertEqual(res2["consecutive_count"], 2)

        # Ciclo 3: Deve atingir o limite de 3 e acionar AUTO-PAUSE!
        res3 = ConflictDetector.evaluate_job(self.db, test_job.id)
        self.assertEqual(res3["status"], "auto_paused")

        # Verifica se o job foi pausado sem ser excluído
        self.db.refresh(test_job)
        self.assertFalse(test_job.is_active)
        self.assertIsNotNone(test_job.pause_reason)
        self.assertIn("Pausado automaticamente", test_job.pause_reason)


if __name__ == "__main__":
    unittest.main()
