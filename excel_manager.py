import ctypes
import gc
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, List

import pythoncom
import win32com.client as win32
import win32con
import win32gui
import win32process

from config import EXCEL_QUIT_GRACE_TIMEOUT

logger = logging.getLogger("ExcelAutomation")

# Constantes do Windows Kernel32
kernel32 = ctypes.windll.kernel32
SYNCHRONIZE = 0x00100000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
WAIT_TIMEOUT = 0x00000102


class ExcelSession:
    """
    Gerenciador de Ciclo de Vida do Processo Microsoft Excel via COM.
    
    Recursos de resiliência:
    - Captura do PID exato do processo EXCEL.EXE spawnado.
    - Configurações headless e supressão de alertas e atualizações visuais.
    - Monitor (watchdog) de diálogos modais para impedir bloqueio de interface.
    - Fechamento garantido em bloco try...finally / Context Manager.
    - Encerramento forçado (force kill) do PID específico caso o Excel trave ou não responda ao Quit().
    """

    def __init__(self, grace_timeout: int = EXCEL_QUIT_GRACE_TIMEOUT):
        self.grace_timeout = grace_timeout
        self.excel = None
        self.pid: Optional[int] = None
        self.hwnd: Optional[int] = None
        self.workbook = None
        self._stop_dialog_watchdog = threading.Event()
        self._watchdog_thread: Optional[threading.Thread] = None

    def __enter__(self):
        logger.info("[EXCEL-MGR] Inicializando thread COM e instância do Excel...")
        pythoncom.CoInitialize()
        try:
            self.excel = win32.DispatchEx("Excel.Application")
            self.hwnd = self.excel.Hwnd
            _, self.pid = win32process.GetWindowThreadProcessId(self.hwnd)
            logger.info(f"[EXCEL-MGR] Excel instanciado com sucesso. PID: {self.pid}, HWND: {self.hwnd}")

            # Configurações de modo não interativo e seguro
            self.excel.Visible = False
            self.excel.DisplayAlerts = False
            self.excel.ScreenUpdating = False
            self.excel.AskToUpdateLinks = False
            self.excel.Interactive = False
            self.excel.FeatureInstall = 0

            # Inicia o monitor de caixas de diálogo modais
            self._start_dialog_watchdog()

            return self
        except Exception as e:
            logger.error(f"[EXCEL-MGR] Falha crítica ao inicializar o Excel: {e}", exc_info=True)
            self.terminate()
            pythoncom.CoUninitialize()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.terminate()
        finally:
            pythoncom.CoUninitialize()

    def _start_dialog_watchdog(self):
        """Inicia thread secundária para detectar e fechar diálogos modais do Excel."""
        self._stop_dialog_watchdog.clear()

        def _monitor():
            while not self._stop_dialog_watchdog.is_set():
                if self.pid and self._is_process_alive(self.pid):
                    self._check_and_dismiss_dialogs()
                time.sleep(2)

        self._watchdog_thread = threading.Thread(target=_monitor, daemon=True, name="ExcelDialogWatchdog")
        self._watchdog_thread.start()

    def _check_and_dismiss_dialogs(self):
        """Varre janelas em busca de diálogos modais (#32770) pertencentes ao processo do Excel."""
        if not self.pid:
            return

        def _enum_cb(hwnd, _):
            if not win32gui.IsWindow(hwnd):
                return True
            try:
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == self.pid:
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name == "#32770":  # Classe padrão de MessageBox / Dialog
                        title = win32gui.GetWindowText(hwnd)
                        logger.warning(
                            f"[EXCEL-MGR] Diálogo modal detectado no Excel (PID {self.pid}): '{title}'. "
                            f"Enviando comando para fechar o diálogo..."
                        )
                        # Tenta enviar IDCANCEL e WM_CLOSE
                        win32gui.PostMessage(hwnd, win32con.WM_COMMAND, win32con.IDCANCEL, 0)
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(_enum_cb, None)
        except Exception:
            pass

    def open_workbook(self, file_path: str | Path):
        """Abre o workbook com parâmetros que evitam bloqueios por links ou recomendações."""
        path_str = str(Path(file_path).resolve())
        logger.info(f"[EXCEL-MGR] Abrindo workbook: {path_str}")

        self.workbook = self.excel.Workbooks.Open(
            path_str,
            UpdateLinks=0,
            ReadOnly=False,
            IgnoreReadOnlyRecommended=True,
            CorruptLoad=1  # xlNormalLoad
        )
        logger.info(f"[EXCEL-MGR] Workbook aberto com sucesso: {self.workbook.Name}")
        return self.workbook

    def disable_background_queries(self) -> List[str]:
        """
        Configura BackgroundQuery = False em todas as conexões OLEDB/ODBC compatíveis.
        Isso força a atualização a ser 100% síncrona, eliminando corridas com a macro.
        Retorna a lista de nomes das conexões configuradas.
        """
        if not self.workbook:
            raise RuntimeError("Nenhum workbook aberto para configurar conexões.")

        configured = []
        total = self.workbook.Connections.Count
        logger.info(f"[EXCEL-MGR] Verificando {total} conexões no workbook...")

        for i in range(1, total + 1):
            conn = self.workbook.Connections.Item(i)
            conn_name = conn.Name
            conn_type = getattr(conn, "Type", None)

            # xlConnectionTypeOLEDB = 1
            if conn_type == 1:
                try:
                    if hasattr(conn, "OLEDBConnection"):
                        conn.OLEDBConnection.BackgroundQuery = False
                        configured.append(conn_name)
                        logger.info(f"[EXCEL-MGR] Conexão OLEDB '{conn_name}': BackgroundQuery definido como False (Síncrono).")
                except Exception as e:
                    # Conexões internas como ThisWorkbookDataModel lançam exceção ao inspecionar OLEDBConnection
                    logger.debug(f"[EXCEL-MGR] Conexão OLEDB '{conn_name}' não suporta BackgroundQuery direto: {e}")

            # xlConnectionTypeODBC = 2
            elif conn_type == 2:
                try:
                    if hasattr(conn, "ODBCConnection"):
                        conn.ODBCConnection.BackgroundQuery = False
                        configured.append(conn_name)
                        logger.info(f"[EXCEL-MGR] Conexão ODBC '{conn_name}': BackgroundQuery definido como False (Síncrono).")
                except Exception as e:
                    logger.debug(f"[EXCEL-MGR] Conexão ODBC '{conn_name}' não suporta BackgroundQuery direto: {e}")

        logger.info(f"[EXCEL-MGR] Total de conexões ajustadas para atualização síncrona: {len(configured)}")
        return configured

    def refresh_with_timeout(self, timeout_seconds: int = 600):
        """
        Executa a atualização de todas as conexões (RefreshAll) com proteção de timeout.
        Se o tempo limite for excedido, o processo Excel é forçosamente finalizado para
        impedir travamento perpétuo.
        """
        if not self.workbook:
            raise RuntimeError("Nenhum workbook aberto para atualização.")

        logger.info(f"[EXCEL-MGR] Iniciando RefreshAll síncrono (Timeout: {timeout_seconds}s)...")
        timeout_occurred = threading.Event()

        def _timeout_watchdog():
            if not timeout_occurred.wait(timeout_seconds):
                logger.critical(
                    f"[EXCEL-MGR] ALERTA DE TIMEOUT: A atualização das queries excedeu o limite de {timeout_seconds}s! "
                    f"Encerrando o processo Excel (PID {self.pid}) para proteger o sistema..."
                )
                self.force_kill()

        watchdog = threading.Thread(target=_timeout_watchdog, daemon=True, name="QueryTimeoutWatchdog")
        watchdog.start()

        start_time = time.time()
        try:
            self.workbook.RefreshAll()
            elapsed = time.time() - start_time
            timeout_occurred.set()
            logger.info(f"[EXCEL-MGR] RefreshAll concluído com sucesso em {elapsed:.2f}s.")
        except Exception as e:
            timeout_occurred.set()
            elapsed = time.time() - start_time
            logger.error(f"[EXCEL-MGR] Erro durante o RefreshAll após {elapsed:.2f}s: {e}", exc_info=True)
            raise

    def run_macro(self, macro_name: str, timeout_seconds: int = 300):
        """
        Executa uma macro VBA no workbook com proteção de timeout.
        Se a macro travar ou exceder o tempo limite, o processo Excel é forçado a encerrar.
        """
        logger.info(f"[EXCEL-MGR] Executando macro: '{macro_name}' (Timeout: {timeout_seconds}s)...")
        timeout_occurred = threading.Event()

        def _macro_timeout_watchdog():
            if not timeout_occurred.wait(timeout_seconds):
                logger.critical(
                    f"[EXCEL-MGR] ALERTA DE TIMEOUT: A execução da macro '{macro_name}' excedeu o limite de {timeout_seconds}s! "
                    f"Encerrando o processo Excel (PID {self.pid}) para proteger o sistema..."
                )
                self.force_kill()

        watchdog = threading.Thread(target=_macro_timeout_watchdog, daemon=True, name="MacroTimeoutWatchdog")
        watchdog.start()

        start_time = time.time()
        try:
            self.excel.Run(macro_name)
            timeout_occurred.set()
            elapsed = time.time() - start_time
            logger.info(f"[EXCEL-MGR] Macro '{macro_name}' executada com sucesso em {elapsed:.2f}s.")
        except Exception as e:
            timeout_occurred.set()
            elapsed = time.time() - start_time
            logger.error(f"[EXCEL-MGR] Erro durante a execução da macro '{macro_name}' após {elapsed:.2f}s: {e}", exc_info=True)
            raise

    def terminate(self):
        """Encerra a sessão do Excel com garantia de eliminação do processo."""
        # 1. Para o monitor de diálogos
        self._stop_dialog_watchdog.set()

        if not self.pid:
            return

        target_pid = self.pid
        logger.info(f"[EXCEL-MGR] Iniciando rotina de encerramento do Excel (PID: {target_pid})...")

        # 2. Fecha o workbook de forma segura se ainda estiver aberto
        if self.workbook:
            try:
                self.workbook.Close(SaveChanges=False)
                logger.info("[EXCEL-MGR] Workbook fechado.")
            except Exception as e:
                logger.debug(f"[EXCEL-MGR] Exceção ao fechar workbook (já pode estar fechado): {e}")
            finally:
                self.workbook = None

        # 3. Tenta fechar outros workbooks e chamar Quit()
        if self.excel:
            try:
                self.excel.DisplayAlerts = False
                for wb in self.excel.Workbooks:
                    try:
                        wb.Close(SaveChanges=False)
                    except Exception:
                        pass
                self.excel.Quit()
                logger.info("[EXCEL-MGR] excel.Quit() chamado com sucesso.")
            except Exception as e:
                logger.warning(f"[EXCEL-MGR] Exceção durante excel.Quit(): {e}")
            finally:
                self.excel = None

        # 4. Libera referências COM do Python
        gc.collect()

        # 5. Aguarda encerramento gracioso dentro do grace_timeout
        deadline = time.time() + self.grace_timeout
        while time.time() < deadline:
            if not self._is_process_alive(target_pid):
                logger.info(f"[EXCEL-MGR] Processo Excel PID {target_pid} finalizado normalmente.")
                self.pid = None
                return
            time.sleep(1)

        # 6. Se ainda estiver ativo, executa force kill do PID exato
        logger.warning(
            f"[EXCEL-MGR] Processo Excel PID {target_pid} não encerrou dentro de {self.grace_timeout}s. "
            f"Executando encerramento forçado (FORCE KILL)..."
        )
        self._force_kill_pid(target_pid)
        self.pid = None

    def force_kill(self):
        """Força a terminação imediata do processo Excel deste gerenciador."""
        if self.pid:
            self._force_kill_pid(self.pid)
            self.pid = None

    @classmethod
    def _force_kill_pid(cls, pid: int):
        """Mata um processo específico pelo PID usando TerminateProcess e taskkill."""
        # 1. Tentativa via API Win32 TerminateProcess
        try:
            handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, 1)
                kernel32.CloseHandle(handle)
        except Exception:
            pass

        time.sleep(0.5)

        # 2. Se ainda persistir, executa taskkill /F
        if cls._is_process_alive(pid):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception as e:
                logger.error(f"[EXCEL-MGR] Falha ao executar taskkill no PID {pid}: {e}")

        time.sleep(0.5)
        if not cls._is_process_alive(pid):
            logger.info(f"[EXCEL-MGR] Processo Excel PID {pid} encerrado com sucesso via force kill.")
        else:
            logger.critical(f"[EXCEL-MGR] ATENÇÃO: Falha ao eliminar o processo PID {pid}!")

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """Verifica de forma confiável via Windows API se o PID ainda está em execução."""
        if not pid:
            return False
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not handle:
            return False
        try:
            return kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
        finally:
            kernel32.CloseHandle(handle)
