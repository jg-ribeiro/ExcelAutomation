from pathlib import Path

# Caminho do workbook da automação
WORKBOOK_PATH = r"\\usa9fs2\CPC_GI\02 - Agrícola\01 - Diário\2026\01 - Placar da Moagem\00 - Moagem - 2026.xlsm"

# Nome da macro a ser disparada após a atualização das queries
MACRO_NAME = "SalvarTodos"

# Horário de execução no scheduler diário (formato 24h HH:MM)
SCHEDULE_TIME = "03:00"

# Timeouts de segurança (em segundos)
# A consulta demora em média 1 minuto; definimos 300s (5 minutos) como margem segura
QUERY_REFRESH_TIMEOUT = 300

# Tempo de tolerância para fechamento gracioso do Excel antes de forçar o kill (segundos)
EXCEL_QUIT_GRACE_TIMEOUT = 15

# Tempo máximo aguardando liberação de lock caso o arquivo esteja em uso temporário (segundos)
FILE_LOCK_RETRY_TIMEOUT = 120

# Intervalo entre tentativas de verificação de lock (segundos)
FILE_LOCK_RETRY_INTERVAL = 5

# Configurações de Log
LOG_DIR = Path(__file__).parent
LOG_FILE = LOG_DIR / "automation.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
