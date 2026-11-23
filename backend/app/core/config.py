import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "automation.db"
LOG_DIR = BASE_DIR
LOG_FILE = LOG_DIR / "automation.log"

# Configurações de Banco de Dados SQLite
DATABASE_URL = f"sqlite:///{DB_PATH}"

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
OVERLAP_SAFETY_THRESHOLD = 0.85      # Se avg_duration >= 85% do intervalo, acusa risco
MIN_RUNS_FOR_CONFLICT_CHECK = 2      # Mínimo de execuções para calcular média confiável
CONSECUTIVE_OVERLAPS_TO_AUTO_PAUSE = 3 # 3 sobreposições consecutivas = pausa automática
AUTO_PAUSE_DEADLINE_HOURS = 24       # Prazo para intervenção do usuário
