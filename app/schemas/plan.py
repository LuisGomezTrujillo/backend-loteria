from typing import List, Optional
from sqlmodel import SQLModel
# Importamos los esquemas de premio necesarios para anidarlos en el plan
from .premio import PremioCreate, PremioRead

class PlanBase(SQLModel):
    nombre: str
    descripcion: Optional[str] = None

class PlanCreate(PlanBase):
    premios: List[PremioCreate]

class PlanRead(PlanBase):
    id: int
    premios: List[PremioRead] = []

class PlanUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None