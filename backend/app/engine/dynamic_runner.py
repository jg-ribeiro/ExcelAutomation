import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Garante acesso aos módulos da raiz (excel_manager e file_guard)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from excel_manager import ExcelSession
from file_guard import wait_for_file_availability, get_file_owner_info
from backend.app.core.config import DEFAULT_FILE_LOCK_INTERVAL

logger = logging.getLogger("ExcelAutomation")


def execute_job(
    job_id: int,
    job_name: str,
    file_path: str,
    macro_name: Optional[str] = "SalvarTodos",
    query_timeout: int = 300,
    lock_timeout: int = 120
) -> Dict[str, Any]:
    """
    Executa o ciclo completo da automação de um job específico reutilizando as
    camadas resilientes comprovadas de ExcelSession e FileGuard.
    
    Retorna um dicionário estruturado com o resultado da execução.
    """
    start_time = time.time()
    captured_pid: Optional[int] = None
    log_messages = []

    def _log(msg: str, level: str = "info"):
        log_messages.append(f"[{level.upper()}] {msg}")
        if level == "critical":
            logger.critical(msg)
        elif level == "error":
            logger.error(msg)
        elif level == "warning":
            logger.warning(msg)
        else:
            logger.info(msg)

    _log("================================================================================")
    _log(f">>> [JOB #{job_id}: {job_name}] INICIANDO ROTINA DE ATUALIZAÇÃO")
    _log(f"    Arquivo: {file_path}")
    _log(f"    Macro: {macro_name or '(Nenhuma)'}")
    _log(f"    Timeout Consulta: {query_timeout}s | Timeout Lock: {lock_timeout}s")
    _log("================================================================================")

    target_path = Path(file_path)

    # 1. Verificação de existência e lock do arquivo
    _log(f"[PASSO 1/5] Verificando disponibilidade e locks do arquivo: {target_path.name}...")
    if not target_path.exists():
        err_msg = (
            f"Arquivo não encontrado ou inacessível no caminho: {file_path}. "
            f"Verifique se o compartilhamento de rede está ativo e se a conta do serviço tem permissão de acesso à pasta."
        )
        _log(err_msg, "error")
        total_time = time.time() - start_time
        return {
            "success": False,
            "status": "failed",
            "duration": total_time,
            "pid": None,
            "error": err_msg,
            "log_snippet": "\n".join(log_messages)
        }

    if not wait_for_file_availability(
        file_path,
        timeout=lock_timeout,
        interval=DEFAULT_FILE_LOCK_INTERVAL
    ):
        owner_info = get_file_owner_info(target_path)
        err_msg = f"Arquivo retido por outro processo após {lock_timeout}s: {target_path.name}. {owner_info}"
        _log(err_msg, "critical")
        total_time = time.time() - start_time
        return {
            "success": False,
            "status": "lock_timeout",
            "duration": total_time,
            "pid": None,
            "error": err_msg,
            "log_snippet": "\n".join(log_messages)
        }

    # 2. Inicialização segura do Excel COM
    _log("[PASSO 2/5] Inicializando sessão segura do Excel via Context Manager...")
    try:
        with ExcelSession() as session:
            captured_pid = session.pid
            _log(f"    -> Instância do Excel criada com sucesso. PID: {captured_pid}")

            # 3. Abertura do workbook e desativação de background queries
            _log("[PASSO 3/5] Abrindo workbook e desativando consultas em segundo plano...")
            session.open_workbook(file_path)
            configured_queries = session.disable_background_queries()
            _log(f"    -> Conexões ajustadas para síncrono: {len(configured_queries)}")

            # 4. Atualização das consultas com timeout
            _log(f"[PASSO 4/5] Executando RefreshAll com timeout de {query_timeout}s...")
            session.refresh_with_timeout(timeout_seconds=query_timeout)

            # 5. Recálculo total, macro e salvamento
            _log("[PASSO 5/5] Recalculando modelo, executando macro e salvando...")
            _log("    -> Executando CalculateFullRebuild()...")
            session.excel.CalculateFullRebuild()

            _log("    -> Pausa de 10s para estabilização de fórmulas e modelo...")
            time.sleep(10)

            if macro_name and macro_name.strip():
                macro_timeout = max(query_timeout, 300)
                _log(f"    -> Disparando macro: '{macro_name}' (timeout: {macro_timeout}s)...")
                session.run_macro(macro_name.strip(), timeout_seconds=macro_timeout)

            _log("    -> Salvando o workbook no disco...")
            session.workbook.Save()
            _log("    -> Workbook salvo com sucesso.")

        total_time = time.time() - start_time
        _log(f">>> [JOB #{job_id}: {job_name}] CONCLUÍDO COM SUCESSO EM {total_time:.2f}s!")
        _log("================================================================================\n")
        return {
            "success": True,
            "status": "success",
            "duration": total_time,
            "pid": captured_pid,
            "error": None,
            "log_snippet": "\n".join(log_messages)
        }

    except Exception as e:
        total_time = time.time() - start_time
        err_msg = f"Falha na execução do Job #{job_id}: {str(e)}"
        _log(err_msg, "error")
        return {
            "success": False,
            "status": "failed",
            "duration": total_time,
            "pid": captured_pid,
            "error": str(e),
            "log_snippet": "\n".join(log_messages)
        }
