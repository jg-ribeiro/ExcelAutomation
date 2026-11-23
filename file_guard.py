import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def get_file_owner_info(file_path: Path) -> str:
    """
    Tenta identificar o usuário que está bloqueando o arquivo
    analisando o arquivo de proprietário temporário do Excel (~$nome.xlsm).
    """
    owner_file = file_path.parent / f"~${file_path.name}"
    if not owner_file.exists():
        return "Arquivo de proprietário (~$...) não encontrado."

    try:
        with open(owner_file, "rb") as f:
            data = f.read(128)
            # Os primeiros bytes contêm o nome do usuário/computador que abriu o arquivo
            chars = []
            for b in data:
                if 32 <= b <= 126:
                    chars.append(chr(b))
            info = "".join(chars).strip()
            return f"Proprietário registrado no lock: '{info}'" if info else "Lock temporário presente (sem nome legível)."
    except Exception as e:
        return f"Não foi possível ler o arquivo de proprietário: {e}"


def is_file_locked(file_path: str | Path) -> bool:
    """
    Verifica se o arquivo está bloqueado para escrita tentando abri-lo em modo r+b.
    Retorna True se estiver bloqueado (em uso por outro processo).
    """
    path = Path(file_path)
    if not path.exists():
        return False

    try:
        # Tenta abrir para leitura e escrita exclusiva
        with open(path, "r+b"):
            return False
    except (PermissionError, OSError):
        return True


def wait_for_file_availability(file_path: str | Path, timeout: int = 120, interval: int = 5) -> bool:
    """
    Aguarda o arquivo ficar liberado até o tempo limite especificado.
    Retorna True se o arquivo estiver acessível e liberado; False se continuar bloqueado.
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"[LOCK-GUARD] Arquivo não encontrado no caminho: {path}")
        return False

    if not is_file_locked(path):
        logger.info(f"[LOCK-GUARD] Arquivo verificado e liberado para abertura: {path.name}")
        return True

    owner_info = get_file_owner_info(path)
    logger.warning(
        f"[LOCK-GUARD] Arquivo '{path.name}' está atualmente bloqueado por outro processo. {owner_info} "
        f"Aguardando liberação por até {timeout}s..."
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        if not is_file_locked(path):
            logger.info(f"[LOCK-GUARD] Arquivo foi liberado com sucesso: {path.name}")
            return True
        logger.debug(f"[LOCK-GUARD] Arquivo continua bloqueado. Tentando novamente em {interval}s...")

    logger.error(
        f"[LOCK-GUARD] TIMEOUT: O arquivo '{path.name}' permaneceu bloqueado após {timeout}s. {owner_info}"
    )
    return False
