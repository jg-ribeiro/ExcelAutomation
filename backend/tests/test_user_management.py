import unittest
from unittest.mock import patch
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.models import User, SystemSetting
from backend.app.main import app


class TestUserManagementAndWhitelist(unittest.TestCase):

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
        self.db.query(User).filter(User.username.in_(["admin_master", "operador_novo", "invasor_ad", "admin_teste_1", "hacker_injetado"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()

    @patch("backend.app.api.routes_auth.authenticate_with_ad")
    def test_whitelist_and_user_crud(self, mock_auth):
        """
        Valida que usuários do AD que NÃO estão autorizados na Whitelist são bloqueados,
        e que o Administrador consegue autorizar, gerenciar papéis e bloquear acessos.
        """
        # 1. Limpa registros de teste
        self.db.query(User).filter(User.username.in_(["admin_master", "operador_novo", "invasor_ad"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()

        mock_auth.return_value = (True, "admin_master", "Admin Master", None)

        # 2. Inicializa o primeiro Administrador via bootstrap
        with patch("backend.app.api.routes_auth.INITIAL_ADMIN_USER", "admin_master"):
            res_admin_login = self.client.post("/api/auth/login", json={"username": "admin_master", "password": "pass"})
            self.assertEqual(res_admin_login.status_code, 200)
            admin_token = res_admin_login.json()["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 3. Usuário do AD NÃO autorizado tenta logar -> DEVE SER REJEITADO COM 403!
        mock_auth.return_value = (True, "invasor_ad", "Colaborador Sem Acesso", None)
        res_invasor = self.client.post("/api/auth/login", json={"username": "invasor_ad", "password": "pass"})
        self.assertEqual(res_invasor.status_code, 403)
        self.assertIn("Acesso não autorizado", res_invasor.json()["detail"])

        # 4. Administrador consulta a lista de usuários
        res_list = self.client.get("/api/users", headers=admin_headers)
        self.assertEqual(res_list.status_code, 200)
        usernames = [u["username"] for u in res_list.json()]
        self.assertIn("admin_master", usernames)

        # 5. Administrador autoriza um novo operador
        res_create = self.client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "operador_novo",
                "display_name": "Novo Operador de Producao",
                "role": "OPERATOR",
                "is_active": True
            }
        )
        self.assertEqual(res_create.status_code, 200)
        op_id = res_create.json()["id"]

        # 6. Agora o operador tenta logar -> DEVE CONSEGUIR!
        mock_auth.return_value = (True, "operador_novo", "Novo Operador de Producao", None)
        res_op_login = self.client.post("/api/auth/login", json={"username": "operador_novo", "password": "pass"})
        self.assertEqual(res_op_login.status_code, 200)
        op_token = res_op_login.json()["access_token"]
        op_headers = {"Authorization": f"Bearer {op_token}"}

        # 7. Operador tenta acessar a rota de gestão de usuários -> DEVE RECEBER 403 FORBIDDEN!
        res_op_forbidden = self.client.get("/api/users", headers=op_headers)
        self.assertEqual(res_op_forbidden.status_code, 403)

        # 8. Administrador bloqueia o acesso do operador
        res_block = self.client.post(f"/api/users/{op_id}/toggle-active", headers=admin_headers)
        self.assertEqual(res_block.status_code, 200)
        self.assertFalse(res_block.json()["is_active"])

        # 9. Operador bloqueado tenta logar novamente -> DEVE RECEBER 403 BLOQUEADO!
        res_blocked_login = self.client.post("/api/auth/login", json={"username": "operador_novo", "password": "pass"})
        self.assertEqual(res_blocked_login.status_code, 403)
        self.assertIn("Acesso bloqueado", res_blocked_login.json()["detail"])

        # 10. Proteção: Administrador tenta bloquear a si mesmo -> DEVE SER IMPEDIDO!
        admin_user = self.db.query(User).filter(User.username == "admin_master").first()
        res_self_block = self.client.post(f"/api/users/{admin_user.id}/toggle-active", headers=admin_headers)
        self.assertEqual(res_self_block.status_code, 400)

        # Limpeza
        self.db.query(User).filter(User.username.in_(["admin_master", "operador_novo", "invasor_ad"])).delete()
        self.db.query(SystemSetting).filter(SystemSetting.key.in_(["bootstrap_completed", "bootstrap_admin_user", "bootstrap_date"])).delete()
        self.db.commit()


if __name__ == "__main__":
    unittest.main()
