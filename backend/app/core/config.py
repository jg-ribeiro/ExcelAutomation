import os
from pathlib import Path
from dotenv import load_dotenv

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Carrega variáveis do arquivo .env caso exista
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DB_PATH = BASE_DIR / "automation.db"
LOG_DIR = BASE_DIR
LOG_FILE = LOG_DIR / "automation.log"

# Configurações de Banco de Dados SQLite
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Controle de Entrega de Arquivos Estáticos pelo Python
SERVE_STATIC = os.getenv("SERVE_STATIC", "true").strip().lower() in ("true", "1", "yes")

# Porta e Host de Operação do Servidor Web
SERVER_PORT = int(os.getenv("PORT") or os.getenv("SERVER_PORT") or "8000")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")

# Configurações do Active Directory (LDAP) da Usina
LDAP_SERVER = os.getenv("LDAP_SERVER", "USA9AD2.usacucar.com.br")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_USE_SSL = os.getenv("LDAP_USE_SSL", "false").strip().lower() in ("true", "1", "yes")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "DC=usacucar,DC=com,DC=br")
LDAP_DOMAIN = os.getenv("LDAP_DOMAIN", "usacucar.com.br")

# Administrador Inicial (usado apenas no primeiro bootstrap)
INITIAL_ADMIN_USER = os.getenv("INITIAL_ADMIN_USER", "joaoribeiro").strip().lower()

# Segurança do Token JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "auteq_usacucar_excel_secret_key_2026_jwt_token_secure")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))

# Configurações de Log
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
RING_BUFFER_CAPACITY = 2000

# Tolerâncias e Timeouts Padrão
DEFAULT_QUERY_REFRESH_TIMEOUT = 300  # 5 minutos
DEFAULT_FILE_LOCK_TIMEOUT = 120      # 2 minutos
DEFAULT_FILE_LOCK_INTERVAL = 5       # 5 segundos
EXCEL_QUIT_GRACE_TIMEOUT = 15        # 15 segundos

# Detecção de Conflitos
OVERLAP_SAFETY_THRESHOLD = 0.85
MIN_RUNS_FOR_CONFLICT_CHECK = 2
CONSECUTIVE_OVERLAPS_TO_AUTO_PAUSE = 3
AUTO_PAUSE_DEADLINE_HOURS = 24
