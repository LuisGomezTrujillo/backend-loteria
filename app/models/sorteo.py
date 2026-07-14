from typing import TYPE_CHECKING, List, Optional
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .plan import PlanPremios
    from .resultado import Resultado
    from .tubo import Tubo
    from .pre_sorteo import PreSorteo

class Sorteo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero_sorteo: str = Field(unique=True, index=True)
    fecha: date
    plan_id: int = Field(foreign_key="planpremios.id")

    plan: Optional["PlanPremios"] = Relationship(back_populates="sorteos")
    resultados: List["Resultado"] = Relationship(back_populates="sorteo")
    tubo: Optional["Tubo"] = Relationship(
        back_populates="sorteo",
        sa_relationship_kwargs={"uselist": False},
    )
    pre_sorteos: List["PreSorteo"] = Relationship(back_populates="sorteo")
