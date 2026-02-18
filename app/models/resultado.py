from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .sorteo import Sorteo
    from .premio import Premio

class Resultado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sorteo_id: int = Field(foreign_key="sorteo.id")
    premio_id: int = Field(foreign_key="premio.id")
    numeros_ganadores: str

    sorteo: Optional["Sorteo"] = Relationship(back_populates="resultados")
    premio: Optional["Premio"] = Relationship(back_populates="resultados")