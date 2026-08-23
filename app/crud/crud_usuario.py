from typing import List, Optional
from sqlmodel import Session, select

from app import models
from app.core import security


def obtener_por_username(session: Session, username: str) -> Optional[models.Usuario]:
    statement = select(models.Usuario).where(models.Usuario.username == username)
    return session.exec(statement).first()


def contar_usuarios(session: Session) -> int:
    return len(session.exec(select(models.Usuario)).all())


def listar_usuarios(session: Session) -> List[models.Usuario]:
    return session.exec(select(models.Usuario)).all()


def crear_usuario(
    session: Session,
    username: str,
    password: str,
    rol: models.RolUsuario,
) -> models.Usuario:
    if obtener_por_username(session, username):
        raise ValueError("Ese nombre de usuario ya existe")

    db_usuario = models.Usuario(
        username=username,
        password_hash=security.hash_password(password),
        rol=rol,
    )
    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)
    return db_usuario


def autenticar(session: Session, username: str, password: str) -> Optional[models.Usuario]:
    usuario = obtener_por_username(session, username)
    if not usuario or not usuario.activo:
        return None
    if not security.verify_password(password, usuario.password_hash):
        return None
    return usuario


def actualizar_usuario(
    session: Session,
    usuario: models.Usuario,
    datos: dict,
) -> models.Usuario:
    if "password" in datos:
        password = datos.pop("password")
        if password:
            usuario.password_hash = security.hash_password(password)

    for key, value in datos.items():
        setattr(usuario, key, value)

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario