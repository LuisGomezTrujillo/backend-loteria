"""
Dependencias de autenticación/autorización.

Lee el JWT del header `Authorization: Bearer <token>` (no de una cookie).

Uso en un router:

    from app.core.deps import get_current_user, require_roles
    from app.models import RolUsuario

    # cualquier usuario logueado (cualquier rol)
    @router.get("/", dependencies=[Depends(get_current_user)])
    def listar(...): ...

    # solo admin y operador
    @router.post("/", dependencies=[Depends(require_roles(RolUsuario.admin, RolUsuario.operador))])
    def crear(...): ...

    # solo admin
    @router.delete("/{id}", dependencies=[Depends(require_roles(RolUsuario.admin))])
    def eliminar(...): ...
"""
from typing import Optional
import jwt
from fastapi import HTTPException, Depends, status, Header
from sqlmodel import Session

from app.core.database import get_session
from app.core import security
from app import models


def _extraer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> models.Usuario:
    token = _extraer_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    try:
        payload = security.decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión expirada, inicia sesión de nuevo")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = session.get(models.Usuario, int(user_id))
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    return usuario


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> Optional[models.Usuario]:
    """Igual que get_current_user, pero devuelve None en vez de lanzar 401.
    Se usa solo en /auth/registro para permitir el bootstrap del primer admin."""
    token = _extraer_token(authorization)
    if not token:
        return None
    try:
        payload = security.decode_token(token)
    except jwt.PyJWTError:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    usuario = session.get(models.Usuario, int(user_id))
    if not usuario or not usuario.activo:
        return None
    return usuario


def require_roles(*roles_permitidos: models.RolUsuario):
    def _dependencia(usuario_actual: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        if usuario_actual.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return usuario_actual
    return _dependencia