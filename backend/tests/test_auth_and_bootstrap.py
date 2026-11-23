import unittest
from unittest.mock import patch
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.models import User, SystemSetting
from backend.app.core.ldap_auth import (
    create_access_token,
    decode_access_token,
    normalize_username
)
from backend.app.main import app


class TestAuthAndBootstrap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        self._cleanup()

    def tearDown(self):
        self._cleanup()
        self.db.close()

    def _cleanup(self):
        self.db.query(User).filter(User.username.in_(["admin_teste_1", "hacker_injetado"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()

    def test_normalize_username(self):
        self.assertEqual(normalize_username("joaoribeiro"), "joaoribeiro")
        self.assertEqual(normalize_username("USACUCAR2000\\joaoribeiro"), "joaoribeiro")
        self.assertEqual(normalize_username("joaoribeiro@usacucar.com.br"), "joaoribeiro")
        self.assertEqual(normalize_username("  JOAORIBEIRO  "), "joaoribeiro")

    def test_jwt_token_encode_decode(self):
        data = {"sub": "testuser", "role": "ADMIN", "name": "Test User"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "testuser")
        self.assertEqual(decoded["role"], "ADMIN")

    @patch("backend.app.api.routes_auth.authenticate_with_ad")
    def test_bootstrap_anti_tamper_lifecycle(self, mock_auth):
        """
        Testa que o usuário inicial definido no ambiente vira ADMIN no primeiro login
        e que tentativas posteriores de mudar o INITIAL_ADMIN_USER são IGNORADAS (Anti-Injeção).
        """
        # Limpa dados de teste anteriores
        self.db.query(User).filter(User.username.in_(["admin_teste_1", "hacker_injetado"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()

        # Configura o mock do AD para aceitar as senhas
        mock_auth.return_value = (True, "admin_teste_1", "Administrador de Teste", None)

        with patch("backend.app.api.routes_auth.INITIAL_ADMIN_USER", "admin_teste_1"):
            # 1. Primeiro login com o INITIAL_ADMIN_USER -> Deve ser promovido a ADMIN
            res1 = self.client.post("/api/auth/login", json={"username": "admin_teste_1", "password": "valid_password"})
            self.assertEqual(res1.status_code, 200)
            user_data = res1.json()["user"]
            self.assertEqual(user_data["role"], "ADMIN")
            self.assertEqual(user_data["username"], "admin_teste_1")

            # Verifica se a trava anti-injeção foi gravada no banco
            setting = self.db.query(SystemSetting).filter(SystemSetting.key == "bootstrap_completed").first()
            self.assertIsNotNone(setting)
            self.assertEqual(setting.value, "true")

        # 2. Cenário de Injeção: Alguém altera o .env em produção para INITIAL_ADMIN_USER="hacker_injetado"
        mock_auth.return_value = (True, "hacker_injetado", "Usuario Malicioso", None)

        with patch("backend.app.api.routes_auth.INITIAL_ADMIN_USER", "hacker_injetado"):
            # 2a. Sem autorização prévia da Whitelist, o usuário é totalmente barrado (403 Forbidden)
            res_blocked = self.client.post("/api/auth/login", json={"username": "hacker_injetado", "password": "valid_password"})
            self.assertEqual(res_blocked.status_code, 403)
            self.assertIn("Acesso não autorizado", res_blocked.json()["detail"])

            # 2b. Mesmo que o usuário tenha autorização como OPERATOR, alterar o INITIAL_ADMIN_USER
            # no .env para o nome dele NÃO o promove a ADMIN, pois o bootstrap está finalizado e travado
            operator_user = User(
                username="hacker_injetado",
                display_name="Operador Comum",
                role="OPERATOR",
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(operator_user)
            self.db.commit()

            res2 = self.client.post("/api/auth/login", json={"username": "hacker_injetado", "password": "valid_password"})
            self.assertEqual(res2.status_code, 200)
            user2_data = res2.json()["user"]

            # PROVA DE SEGURANÇA: Permanece OPERATOR, a trava do SQLite protegeu contra injeção de privilégio!
            self.assertEqual(user2_data["role"], "OPERATOR")
            self.assertNotEqual(user2_data["role"], "ADMIN")

        # Limpeza
        self.db.query(User).filter(User.username.in_(["admin_teste_1", "hacker_injetado"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()


if __name__ == "__main__":
    unittest.main()
