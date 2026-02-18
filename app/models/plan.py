from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship

# Esto solo lo lee el editor de código, no se ejecuta en tiempo real
if TYPE_CHECKING:
    from .premio import Premio
    from .sorteo import Sorteo

class PlanPremios(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    descripcion: Optional[str] = None

    premios: List["Premio"] = Relationship(back_populates="plan")
    sorteos: List["Sorteo"] = Relationship(back_populates="plan")