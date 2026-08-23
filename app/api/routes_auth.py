from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from sqlmodel import Session

from app.core.database import get_session
from app.core import security
from app.core.deps import get_current_user, get_current_user_optional, require_roles
from app import models, schemas
from app.crud import crud_usuario as crud

router = APIRouter(prefix="/auth", tags=["Autenticación"])


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


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    datos: schemas.UsuarioLogin,
    session: Session = Depends(get_session),
):
    """
    Devuelve los datos del usuario + un JWT (access_token) en el CUERPO de
    la respuesta. El frontend debe guardarlo (localStorage) y reenviarlo en
    cada petición como header 'Authorization: Bearer <access_token>'.

    No se usa cookie a propósito: frontend (Vercel) y backend (Render) son
    dominios raíz distintos, y los navegadores modernos bloquean por
    defecto las cookies "de terceros" entre sitios así, sin importar los
    ajustes de SameSite/Secure.
    """
    usuario = crud.autenticar(session, datos.username, datos.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = security.create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})

    return schemas.LoginResponse(
        id=usuario.id,
        username=usuario.username,
        rol=usuario.rol,
        activo=usuario.activo,
        creado_en=usuario.creado_en,
        access_token=token,
    )


@router.post("/logout")
def logout():
    """
    Como el JWT es stateless (no se guarda en el servidor), no hay nada que
    invalidar acá. El logout real ocurre en el frontend, borrando el token
    de localStorage. Este endpoint existe por simetría / por si más
    adelante se agrega una lista de tokens revocados.
    """
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