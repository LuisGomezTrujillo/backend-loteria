from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .plan import PlanPremios
    from .resultado import Resultado

class Premio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="planpremios.id")
    titulo: str
    valor: str
    cantidad_balotas: int

    plan: Optional["PlanPremios"] = Relationship(back_populates="premios")
    resultados: List["Resultado"] = Relationship(back_populates="premio")