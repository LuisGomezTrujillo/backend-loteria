from typing import Optional
from sqlmodel import SQLModel

class PremioBase(SQLModel):
    titulo: str
    valor: str
    cantidad_balotas: int

class PremioCreate(PremioBase):
    pass

class PremioRead(PremioBase):
    id: int
    plan_id: int

class PremioUpdate(SQLModel):
    titulo: Optional[str] = None
    valor: Optional[str] = None
    cantidad_balotas: Optional[int] = None