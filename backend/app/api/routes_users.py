from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import User, UserCreate, UserUpdate, UserOut
from backend.app.core.ldap_auth import require_admin, normalize_username

router = APIRouter(prefix="/api/users", tags=["Usuários e Permissões"])


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Lista todos os usuários com acesso autorizado ao sistema (Apenas ADMIN)."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut)
def authorize_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Pré-autoriza um colaborador do AD a acessar a aplicação.
    Define se ele atuará como OPERADOR ou ADMINISTRADOR.
    """
    clean_username = normalize_username(payload.username)
    if not clean_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário inválido."
        )

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O usuário '{clean_username}' já possui autorização cadastrada."
        )

    display_name = payload.display_name.strip() if payload.display_name else clean_username.title()

    new_user = User(
        username=clean_username,
        display_name=display_name,
        role=payload.role,
        is_active=payload.is_active,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserOut.model_validate(new_user)


@router.put("/{user_id}", response_model=UserOut)
def update_user_authorization(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Atualiza o papel (ADMIN/OPERATOR) ou status de ativação de um usuário."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Impede que o próprio admin logado remova seu perfil de ADMIN ou se desative
    if user.id == admin.id:
        if payload.role and payload.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode revogar seu próprio privilégio de Administrador."
            )
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode desativar seu próprio acesso."
            )

    data = payload.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(user, field, val)

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}")
def revoke_user_authorization(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Revoga o acesso e exclui o usuário da lista de autorizados."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode excluir sua própria conta de Administrador."
        )

    db.delete(user)
    db.commit()
    return {"success": True, "message": f"Acesso do usuário '{user.username}' revogado com sucesso."}


@router.post("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Ativa ou bloqueia temporariamente o acesso de um usuário."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user.id == admin.id and user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta de Administrador."
        )

    user.is_active = not user.is_active
    db.commit()

    return {
        "success": True,
        "is_active": user.is_active,
        "message": f"Usuário '{user.username}' {'ativado' if user.is_active else 'bloqueado'} com sucesso."
    }
