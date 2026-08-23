from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class RolUsuario(str, Enum):
    admin = "admin"
    operador = "operador"
    consulta = "consulta"


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    rol: RolUsuario = Field(default=RolUsuario.consulta, nullable=False)
    activo: bool = Field(default=True, nullable=False)
    creado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))