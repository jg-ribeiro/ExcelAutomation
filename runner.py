import logging
from logging.handlers import RotatingFileHandler
import sys
import time
from pathlib import Path

from config import (
    WORKBOOK_PATH,
    MACRO_NAME,
    QUERY_REFRESH_TIMEOUT,
    FILE_LOCK_RETRY_TIMEOUT,
    FILE_LOCK_RETRY_INTERVAL,
    LOG_FILE,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
)
from excel_manager import ExcelSession
from file_guard import wait_for_file_availability


def setup_logger() -> logging.Logger:
    """Configura o logger com rotação de arquivos e saída no console."""
    logger = logging.getLogger("ExcelAutomation")
    logger.setLevel(logging.INFO)

    # Evita adicionar múltiplos handlers se já estiver configurado
    if not logger.handlers:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler com Rotação (evita que o log cresça infinitamente)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def run() -> bool:
    """
    Executa o ciclo completo da automação com todas as camadas de segurança.
    Retorna True se concluído com sucesso, ou lança uma exceção em caso de erro.
    """
    start_time = time.time()
    logger.info("================================================================================")
    logger.info(">>> INICIANDO ROTINA DE ATUALIZAÇÃO DO WORKBOOK")
    logger.info(f"    Alvo: {WORKBOOK_PATH}")
    logger.info(f"    Macro: {MACRO_NAME}")
    logger.info("================================================================================")

    # 1. Pré-checagem de disponibilidade e locks do arquivo
    logger.info("[PASSO 1/5] Verificando disponibilidade e locks do arquivo...")
    if not wait_for_file_availability(
        WORKBOOK_PATH,
        timeout=FILE_LOCK_RETRY_TIMEOUT,
        interval=FILE_LOCK_RETRY_INTERVAL
    ):
        error_msg = f"Arquivo indisponível ou retido por outro processo após {FILE_LOCK_RETRY_TIMEOUT}s: {WORKBOOK_PATH}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    # 2. Inicialização da sessão segura do Excel
    logger.info("[PASSO 2/5] Inicializando sessão segura do Excel via Context Manager...")
    with ExcelSession() as session:
        # 3. Abertura do workbook e configuração das conexões para síncrono
        logger.info("[PASSO 3/5] Abrindo o workbook e desativando consultas em segundo plano...")
        session.open_workbook(WORKBOOK_PATH)
        session.disable_background_queries()

        # 4. Atualização segura com timeout
        logger.info(f"[PASSO 4/5] Executando RefreshAll com timeout de {QUERY_REFRESH_TIMEOUT}s...")
        session.refresh_with_timeout(timeout_seconds=QUERY_REFRESH_TIMEOUT)

        # 5. Recálculo total, execução da Macro e Salvamento
        logger.info("[PASSO 5/5] Recalculando, executando macro e salvando alterações...")
        logger.info("    -> Executando CalculateFullRebuild()...")
        session.excel.CalculateFullRebuild()

        logger.info("    -> Pausa de 10s para estabilização de fórmulas e modelo...")
        time.sleep(10)

        logger.info(f"    -> Disparando macro: '{MACRO_NAME}'...")
        session.run_macro(MACRO_NAME)

        logger.info("    -> Salvando o workbook no disco...")
        session.workbook.Save()
        logger.info("    -> Workbook salvo com sucesso.")

    total_time = time.time() - start_time
    logger.info(f">>> ROTINA CONCLUÍDA COM SUCESSO EM {total_time:.2f}s!")
    logger.info("================================================================================\n")
    return True


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.critical(f"Execução finalizada com erro: {e}", exc_info=True)
        sys.exit(1)
