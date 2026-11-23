"""
Agendador de Tarefas Diário para Automação do Excel.
Executa de forma resiliente, blindado contra exceções para não interromper os dias seguintes.
"""
import argparse
import datetime
import sys
import time

import schedule

from config import SCHEDULE_TIME
from runner import run, logger


def safe_run():
    """
    Invoca a rotina de automação capturando qualquer exceção,
    garantindo que o loop do scheduler permaneça vivo para os dias seguintes.
    """
    logger.info(f"[SCHEDULER] Disparando execução agendada das {SCHEDULE_TIME}...")
    try:
        run()
        logger.info("[SCHEDULER] Execução diária finalizada com êxito.")
    except Exception as e:
        logger.critical(f"[SCHEDULER] Falha crítica na execução agendada: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="Agendador resiliente da automação do Excel")
    parser.add_argument(
        "--now",
        "--run-now",
        dest="run_now",
        action="store_true",
        help="Executa a rotina imediatamente uma vez antes de entrar no agendamento"
    )
    args = parser.parse_args()

    logger.info("================================================================================")
    logger.info(f"[SCHEDULER] Iniciando serviço de agendamento da automação.")
    logger.info(f"[SCHEDULER] Horário programado diariamente: {SCHEDULE_TIME}")
    logger.info("================================================================================")

    if args.run_now:
        logger.info("[SCHEDULER] Flag --run-now detectada. Executando rotina imediatamente...")
        safe_run()

    # Registra o job no agendador
    schedule.every().day.at(SCHEDULE_TIME).do(safe_run)
    logger.info(f"[SCHEDULER] Tarefa diária registrada para as {SCHEDULE_TIME}.")

    heartbeat_counter = 0
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Checa a cada 60 segundos por tarefas pendentes
            heartbeat_counter += 1

            # Log de heartbeat a cada 6 horas (360 minutos = 360 iterações de 60s)
            if heartbeat_counter >= 360:
                next_run = schedule.next_run()
                logger.info(f"[SCHEDULER-HEARTBEAT] Agendador ativo. Próxima execução prevista: {next_run}")
                heartbeat_counter = 0

        except KeyboardInterrupt:
            logger.info("[SCHEDULER] Interrupção manual solicitada (KeyboardInterrupt). Encerrando serviço...")
            break
        except Exception as e:
            logger.error(f"[SCHEDULER] Exceção inesperada no loop principal: {e}", exc_info=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
