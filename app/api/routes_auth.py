from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Response

from sqlmodel import Session

from app.core.database import get_session
from app.core import security
from app.core.deps import get_current_user, get_current_user_optional, require_roles
from app import models, schemas
from app.crud import crud_usuario as crud

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Ajustes de la cookie de sesión.
# secure=True + samesite="none" es obligatorio porque el frontend (Vercel)
# y el backend (Render) están en dominios distintos. Ambos ya sirven HTTPS,
# así que esto funciona en producción. En localhost (http) el navegador
# rechazará la cookie con estos ajustes: para probar login en localhost
# necesitas correr el frontend también bajo HTTPS, o bajar temporalmente
# a samesite="lax"/secure=False solo en desarrollo (ver nota al final).
COOKIE_KWARGS = dict(
    httponly=True,
    secure=True,
    samesite="none",
    max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/",
)


@router.post("/registro", response_model=schemas.UsuarioRead)
def registrar_usuario(
    datos: schemas.UsuarioCreate,
    session: Session = Depends(get_session),
    usuario_actual: Optional[models.Usuario] = Depends(get_current_user_optional),
):
    """
    Bootstrap: si todavía no hay ningún usuario en la base de datos, este
    endpoint crea el primer usuario como admin, SIN necesidad de estar
    autenticado. Después de eso, solo un admin logueado puede registrar
    usuarios nuevos (y elige el rol).
    """
    if crud.contar_usuarios(session) > 0:
        if usuario_actual is None or usuario_actual.rol != models.RolUsuario.admin:
            raise HTTPException(status_code=403, detail="Solo un administrador puede registrar nuevos usuarios")
        rol_final = datos.rol
    else:
        rol_final = models.RolUsuario.admin

    try:
        return crud.crear_usuario(session, datos.username, datos.password, rol_final)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=schemas.UsuarioRead)
def login(
    datos: schemas.UsuarioLogin,
    response: Response,
    session: Session = Depends(get_session),
):
    usuario = crud.autenticar(session, datos.username, datos.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = security.create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    response.set_cookie(key=security.COOKIE_NAME, value=token, **COOKIE_KWARGS)
    return usuario


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=security.COOKIE_NAME, path="/")
    return {"ok": True, "message": "Sesión cerrada"}


@router.get("/me", response_model=schemas.UsuarioRead)
def quien_soy(usuario_actual: models.Usuario = Depends(get_current_user)):
    return usuario_actual


# --- GESTIÓN DE USUARIOS (solo admin) ---

@router.get("/usuarios", response_model=List[schemas.UsuarioRead])
def listar_usuarios(
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(models.RolUsuario.admin)),
):
    return crud.listar_usuarios(session)


@router.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioRead)
def actualizar_usuario(
    usuario_id: int,
    datos: schemas.UsuarioUpdate,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(models.RolUsuario.admin)),
):
    usuario = session.get(models.Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    datos_dict = datos.model_dump(exclude_unset=True)
    return crud.actualizar_usuario(session, usuario, datos_dict)


@router.delete("/usuarios/{usuario_id}")
def desactivar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    admin_actual: models.Usuario = Depends(require_roles(models.RolUsuario.admin)),
):
    """No borramos usuarios de la BD (para no romper historiales/auditoría),
    solo los desactivamos."""
    if usuario_id == admin_actual.id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propio usuario")

    usuario = session.get(models.Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.activo = False
    session.add(usuario)
    session.commit()
    return {"ok": True, "message": f"Usuario '{usuario.username}' desactivado"}