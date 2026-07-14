"""
Modelo: PreSorteo

Representa una "Prueba" realizada antes de un sorteo oficial (ensayo del
sorteo real), SIN relación con el Plan de Premios. Cada sorteo puede tener
entre 5 y 10 pruebas, numeradas secuencialmente de 1 a 10 dentro de ese
sorteo (numero_prueba, asignado automáticamente al crear).

Cada prueba produce un único resultado (numeros_ganadores), con la misma
cantidad de balotas/cifras que se usa en los premios reales del sorteo:
- 6 balotas -> 7 cifras totales (4 balotas de 1 dígito + serie de 2 dígitos
  + 1 balota de 1 dígito), igual que el Premio Mayor.
- 4 balotas -> 4 cifras totales, igual que los premios secos.

cantidad_balotas se define al crear la prueba (por defecto 6) y ya no
depende de ningún registro de Premio.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from .sorteo import Sorteo


class PreSorteo(SQLModel, table=True):
    __tablename__ = "pre_sorteo"
    __table_args__ = (
        UniqueConstraint("sorteo_id", "numero_prueba", name="uq_presorteo_sorteo_numero"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    sorteo_id: int = Field(foreign_key="sorteo.id", index=True)
    numero_prueba: int  # 1..10, secuencial dentro del sorteo
    cantidad_balotas: int = Field(default=6)  # 4 o 6, igual que Premio.cantidad_balotas
    numeros_ganadores: Optional[str] = Field(default=None)
    fecha_hora: Optional[datetime] = Field(default_factory=datetime.utcnow)

    sorteo: Optional["Sorteo"] = Relationship(back_populates="pre_sorteos")