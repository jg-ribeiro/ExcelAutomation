from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import INITIAL_ADMIN_USER
from backend.app.core.database import get_db
from backend.app.core.models import User, SystemSetting, UserLogin, UserOut, TokenOut
from backend.app.core.ldap_auth import (
    authenticate_with_ad,
    create_access_token,
    get_current_user,
    normalize_username
)

logger = logging.getLogger("ExcelAutomation")

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.get("/bootstrap-status")
def get_bootstrap_status(db: Session = Depends(get_db)):
    """Retorna se o provisionamento inicial do primeiro administrador já foi realizado."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == "bootstrap_completed").first()
    is_completed = setting is not None and setting.value.lower() == "true"
    
    return {
        "bootstrap_completed": is_completed,
        "initial_admin_user": INITIAL_ADMIN_USER if not is_completed else None
    }


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica o usuário no Active Directory da Usina.
    Aplica mecanismo seguro de bootstrap anti-injeção para o primeiro administrador.
    """
    success, clean_username, display_name, err_msg = authenticate_with_ad(
        raw_username=payload.username,
        password=payload.password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err_msg or "Usuário ou senha incorretos no Active Directory."
        )

    # 1. Verifica se a trava de bootstrap já foi ativada no banco
    bootstrap_setting = db.query(SystemSetting).filter(SystemSetting.key == "bootstrap_completed").first()
    is_bootstrap_completed = bootstrap_setting is not None and bootstrap_setting.value.lower() == "true"

    user = db.query(User).filter(User.username == clean_username).first()

    now = datetime.utcnow()

    if not user:
        # Se for um novo usuário, determina o papel inicial
        assigned_role = "OPERATOR"

        # O primeiro admin só é concedido se o bootstrap AINDA estiver pendente
        if not is_bootstrap_completed:
            if clean_username == INITIAL_ADMIN_USER:
                assigned_role = "ADMIN"
                # Trava o bootstrap permanentemente no SQLite
                if not bootstrap_setting:
                    bootstrap_setting = SystemSetting(
                        key="bootstrap_completed",
                        value="true",
                        description="Indica se o administrador inicial já foi ativado via AD"
                    )
                    db.add(bootstrap_setting)
                else:
                    bootstrap_setting.value = "true"

                admin_setting = SystemSetting(
                    key="bootstrap_admin_user",
                    value=clean_username,
                    description="Usuário que concluiu o bootstrap inicial"
                )
                db.add(admin_setting)

                date_setting = SystemSetting(
                    key="bootstrap_date",
                    value=now.isoformat(),
                    description="Data/hora da conclusão do bootstrap"
                )
                db.add(date_setting)

                logger.info(
                    f"[AUTH] BOOTSTRAP CONCLUÍDO COM SUCESSO: Usuário '{clean_username}' promovido a ADMIN. "
                    f"A trava de segurança foi ativada. Alterações futuras no .env serão ignoradas."
                )
        else:
            # Bootstrap já foi realizado anteriormente: qualquer novo usuário entra como OPERATOR
            logger.info(
                f"[AUTH] Bootstrap já finalizado anteriormente. Novo usuário '{clean_username}' criado como OPERATOR."
            )

        user = User(
            username=clean_username,
            display_name=display_name or clean_username.title(),
            role=assigned_role,
            is_active=True,
            last_login_at=now,
            created_at=now
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    else:
        # Usuário já existe
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso desativado para este usuário. Contate o administrador."
            )

        user.last_login_at = now
        if display_name and not user.display_name:
            user.display_name = display_name
        db.commit()

    # Gera token de acesso JWT
    token_payload = {
        "sub": user.username,
        "role": user.role,
        "name": user.display_name or user.username
    }
    token = create_access_token(token_payload)

    return TokenOut(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário autenticado a partir do token de sessão."""
    return UserOut.model_validate(current_user)
