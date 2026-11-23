from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple, Dict, Any
import jwt
from ldap3 import Server, Connection, SIMPLE, ALL, NTLM
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.config import (
    LDAP_SERVER,
    LDAP_PORT,
    LDAP_USE_SSL,
    LDAP_BASE_DN,
    LDAP_DOMAIN,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
)
from backend.app.core.database import get_db
from backend.app.core.models import User

logger = logging.getLogger("ExcelAutomation")

security = HTTPBearer(auto_error=False)


def normalize_username(raw_username: str) -> str:
    """Normaliza o nome do usuário removendo domínios ou sufixos."""
    username = raw_username.strip().lower()
    if "\\" in username:
        username = username.split("\\", 1)[1]
    if "@" in username:
        username = username.split("@", 1)[0]
    return username


def authenticate_with_ad(raw_username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Autentica as credenciais fornecidas diretamente no Active Directory da Usina.
    Retorna: (sucesso: bool, clean_username: str, display_name: str, error_msg: str)
    """
    clean_username = normalize_username(raw_username)
    if not clean_username or not password:
        return False, clean_username, None, "Usuário e senha são obrigatórios."

    # Tenta autenticação via UPN: usuario@usacucar.com.br
    upn = f"{clean_username}@{LDAP_DOMAIN}"

    logger.info(f"[AD-AUTH] Tentando autenticação LDAP para '{clean_username}' em {LDAP_SERVER}:{LDAP_PORT}...")

    try:
        server = Server(
            LDAP_SERVER,
            port=LDAP_PORT,
            use_ssl=LDAP_USE_SSL,
            get_info=ALL,
            connect_timeout=6
        )

        conn = Connection(
            server,
            user=upn,
            password=password,
            authentication=SIMPLE,
            auto_bind=False,
            read_only=True
        )

        bind_success = conn.bind()

        if not bind_success:
            # Tenta alternativamente com formato de domínio antigo: USACUCAR2000\usuario
            alt_user = f"USACUCAR2000\\{clean_username}"
            conn_alt = Connection(
                server,
                user=alt_user,
                password=password,
                authentication=SIMPLE,
                auto_bind=False,
                read_only=True
            )
            bind_success = conn_alt.bind()
            if not bind_success:
                logger.warning(f"[AD-AUTH] Falha de bind para '{clean_username}': credenciais inválidas no AD.")
                return False, clean_username, None, "Credenciais inválidas no Active Directory."

        display_name = clean_username.title()

        # Opcional: tenta buscar o displayName real nos atributos LDAP do AD
        try:
            conn.search(
                search_base=LDAP_BASE_DN,
                search_filter=f"(sAMAccountName={clean_username})",
                attributes=["displayName", "mail", "cn"]
            )
            if conn.entries:
                entry = conn.entries[0]
                if hasattr(entry, "displayName") and entry.displayName.value:
                    display_name = str(entry.displayName.value)
        except Exception:
            pass

        try:
            conn.unbind()
        except Exception:
            pass

        logger.info(f"[AD-AUTH] Autenticação bem-sucedida para '{clean_username}' ({display_name}).")
        return True, clean_username, display_name, None

    except Exception as e:
        err_msg = f"Erro de comunicação com o controlador de domínio AD: {str(e)}"
        logger.error(f"[AD-AUTH] Exceção ao conectar no LDAP: {e}", exc_info=True)
        return False, clean_username, None, err_msg


def create_access_token(data: Dict[str, Any]) -> str:
    """Gera token JWT assinado com tempo de expiração."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica e valida assinatura e expiração do token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retorna o usuário autenticado caso um token válido seja fornecido, ou None."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None

    username = payload["sub"]
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    return user


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Exige que a requisição contenha um token de autenticação válido."""
    user = get_current_user_optional(auth, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão não autenticada ou expirada. Por favor, faça login com suas credenciais do AD.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
