import win32com.client as win32
import logging
from pathlib import Path
import sys
import time

# Configurar logging
log_dir = Path(__file__).parent
log_file = log_dir / "automation.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def listar_conexoes_em_refresh(workbook):
    conexoes = []

    try:
        total = workbook.Connections.Count
    except Exception as e:
        logger.error(f'Não foi possível acessar as conexões do workbook: {e}')
        return conexoes  # retorna lista vazia

    for i in range(1, total + 1):
        try:
            conn = workbook.Connections.Item(i)

            if hasattr(conn, "Refreshing") and conn.Refreshing:
                conexoes.append(conn.Name)
                continue

            if hasattr(conn, "OLEDBConnection"):
                if conn.OLEDBConnection.Refreshing:
                    conexoes.append(conn.Name)
                    continue

            if hasattr(conn, "ODBCConnection"):
                if conn.ODBCConnection.Refreshing:
                    conexoes.append(conn.Name)
                    continue

        except Exception:
            continue

    return conexoes


def run():
    print('[INFO] - Iniciando automação')
    excel = win32.DispatchEx("Excel.Application")
    excel.DisplayAlerts = False
    excel.Visible = False

    logger.info('Excel iniciado com sucesso')

    try:
        logger.info(f'Tentando abrir workbook')
        workbook = excel.Workbooks.Open(r'\\usa9fs2\CPC_GI\02 - Agrícola\01 - Diário\2026\01 - Placar da Moagem\00 - Moagem - 2026.xlsm')
        logger.info('Workbook aberto com sucesso')
    except Exception as er:
        logger.error(f'Erro ao abrir Workbook: {er}', exc_info=True)
        excel.Quit()
        sys.exit(1)

    workbook.RefreshAll()
    logger.info('RefreshAll iniciado')

    while True:
        conexoes = listar_conexoes_em_refresh(workbook)

        if not conexoes:
            logger.info('Todas as conexões finalizadas o refresh')

            # FORÇA recálculo total (Power Pivot + fórmulas)
            excel.CalculateFullRebuild()
            logger.info('CalculateFullRebuild executado')
            
            time.sleep(10)

            excel.Run('SalvarTodos')
            logger.info('Macro SalvarTodos executada')

            workbook.Save()
            logger.info('Workbook salvo com sucesso')
            break
        else:
            logger.debug(f'Aguardando conexões: {", ".join(conexoes)}')

    excel.DisplayAlerts = False
    excel.Quit()
    logger.info('Excel fechado com sucesso')


if __name__ == "__main__":
    run()