"""
Módulo de compatibilidade com a versão anterior da automação.
Redireciona a execução para o novo runner resiliente (runner.py).
"""
import sys
from runner import run, logger

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.critical(f"Execução via mock_simple finalizada com erro: {e}", exc_info=True)
        sys.exit(1)
