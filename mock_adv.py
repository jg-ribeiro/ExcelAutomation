import win32com.client as win32
import time
import logging
from datetime import datetime
import os
import sys

# ===============================
# CONFIGURAÇÕES
# ===============================

def diretorio_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # pasta do EXE
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = diretorio_base()

PASTA_ARQUIVOS = os.path.join(BASE_DIR, "ArquivosExcel")
PASTA_LOG = os.path.join(BASE_DIR, "Logs")

os.makedirs(PASTA_ARQUIVOS, exist_ok=True)
os.makedirs(PASTA_LOG, exist_ok=True)

ARQUIVOS_EXCEL = [
    os.path.join(PASTA_ARQUIVOS, f)
    for f in os.listdir(PASTA_ARQUIVOS)
    if f.lower().endswith(".xlsx") and not f.startswith("~$")
]

ARQUIVOS_EXCEL.sort()

TEMPO_MAX_REFRESH = 60 * 35  # 35 minutos
INTERVALO_VERIFICACAO = 15
MAX_TENTATIVAS = 5

# ===============================
# LOG
# ===============================
data_log = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"{PASTA_LOG}\\refresh_{data_log}.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def listar_conexoes_em_refresh(workbook):
    conexoes = []

    try:
        total = workbook.Connections.Count
    except Exception as e:
        logging.warning(f"Não foi possível ler Connections: {e}")
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

def fechar_workbook_seguro(workbook):
    try:
        workbook.Close(False)
    except Exception as e:
        logging.error(f"Erro ao fechar workbook: {e}")

# ===============================
# PROCESSAMENTO DO ARQUIVO
# ===============================

def processar_arquivo(caminho_arquivo, excel):
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        inicio = time.time()
        log("=" * 80)
        log(f"Arquivo: {caminho_arquivo}")
        log(f"Tentativa {tentativa} de {MAX_TENTATIVAS}")

        workbook = None

        try:
            workbook = excel.Workbooks.Open(caminho_arquivo)
            log("Após abrir o excel, estou aguardando 2 segundos antes de disparar o cálculo...")
            time.sleep(2)

            log("Disparando RefreshAll()...")
            workbook.RefreshAll()

            while True:
                log("Validar as conexões...")
                conexoes = listar_conexoes_em_refresh(workbook)
                log(f"Atualizando as seguintes conexões: {conexoes}")

                if not conexoes:
                    log("Power Query finalizado...")

                    # FORÇA recálculo total (Power Pivot + fórmulas)
                    log("Executando CalculateFullRebuild()...")
                    excel.CalculateFullRebuild()

                    workbook.Save()
                    log("Arquivo salvo...")
                    return  # sucesso

                if time.time() - inicio > TEMPO_MAX_REFRESH:
                    raise TimeoutError("Tempo máximo de refresh excedido...")

                log("Power Query ainda em execução...")
                time.sleep(INTERVALO_VERIFICACAO)

        except Exception as e:
            log(f"ERRO inesperado: {str(e)}")
            if workbook:
                fechar_workbook_seguro(workbook)
                time.sleep(5)

        finally:
            if workbook:
                log("Fechando workbook (finally)")
                fechar_workbook_seguro(workbook)
                time.sleep(5)

        log("Aguardando antes de nova tentativa...")
        time.sleep(5)

    # Se chegou aqui, falhou todas as tentativas
    log(f"FALHA DEFINITIVA após {MAX_TENTATIVAS} tentativas: {caminho_arquivo}")

# ===============================
# EXECUÇÃO PRINCIPAL
# ===============================

log("Iniciando automação Power Query")

excel = win32.DispatchEx("Excel.Application")
excel.DisplayAlerts = False

try:
    for arquivo in ARQUIVOS_EXCEL:
        if "Totalizadora x Produtiva" in arquivo:
            excel.Visible = True
        else:
            excel.Visible = False

        processar_arquivo(arquivo, excel)
finally:
    log("Encerrando Excel")
    try:
        excel.DisplayAlerts = False
        excel.Quit()
    except:
        pass
    finally:
        excel = None
        time.sleep(3)

log("Automação finalizada")