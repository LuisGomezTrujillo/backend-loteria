from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models import RolUsuario


class UsuarioLogin(BaseModel):
    username: str
    password: str


class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: RolUsuario = RolUsuario.consulta

    @field_validator("username")
    @classmethod
    def username_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El usuario debe tener al menos 3 caracteres")
        return v

    @field_validator("password")
    @classmethod
    def password_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    password: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

    @field_validator("password")
    @classmethod
    def password_minima(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class UsuarioRead(BaseModel):
    id: int
    username: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True