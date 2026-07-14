"""
Modelo: Tubos

Almacena, para cada sorteo, qué tubo (de los 26 disponibles) fue asignado
a cada una de las 6 urnas de balotas:

- Urnas 1 a 4: un tubo cualquiera entre el 1 y el 17 (balotas 0-9).
- Urna 5: uno de los 3 conjuntos de 3 tubos consecutivos entre el 18 y el 26
  ("18-19-20", "21-22-23", "24-25-26"), cuyas balotas van de 00 a 39.
- Urna 6: un tubo entre el 1 y el 17 que NO haya sido usado en las urnas 1-4.

Relación 1 a 1 con Sorteo (cada sorteo tiene una única configuración de tubos).
"""
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .sorteo import Sorteo


class Tubo(SQLModel, table=True):
    __tablename__ = "tubo"

    id: Optional[int] = Field(default=None, primary_key=True)
    sorteo_id: int = Field(foreign_key="sorteo.id", unique=True, index=True)

    tubo_urna1: str
    tubo_urna2: str
    tubo_urna3: str
    tubo_urna4: str
    tubos_urna5: str
    tubo_urna6: str

    sorteo: Optional["Sorteo"] = Relationship(
        back_populates="tubo",
        sa_relationship_kwargs={"uselist": False},
    )