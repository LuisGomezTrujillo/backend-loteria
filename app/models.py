from typing import List, Optional
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

# Tabla: Plan de Premios
class PlanPremios(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    descripcion: Optional[str] = None

    premios: List["Premio"] = Relationship(back_populates="plan")
    sorteos: List["Sorteo"] = Relationship(back_populates="plan")


# Tabla: Premios individuales
class Premio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="planpremios.id")
    titulo: str
    valor: str
    cantidad_balotas: int

    plan: Optional["PlanPremios"] = Relationship(back_populates="premios")
    resultados: List["Resultado"] = Relationship(back_populates="premio")


# Tabla: Sorteos (Instancias de juego)
class Sorteo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # CAMBIO IMPORTANTE: numero_sorteo es String para aceptar "001", "Extra", etc.
    numero_sorteo: str = Field(unique=True, index=True)
    fecha: date
    plan_id: int = Field(foreign_key="planpremios.id")

    plan: Optional["PlanPremios"] = Relationship(back_populates="sorteos")
    resultados: List["Resultado"] = Relationship(back_populates="sorteo")


# Tabla: Resultados (Ganadores)
class Resultado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sorteo_id: int = Field(foreign_key="sorteo.id")
    premio_id: int = Field(foreign_key="premio.id")
    numeros_ganadores: str

    sorteo: Optional["Sorteo"] = Relationship(back_populates="resultados")
    premio: Optional["Premio"] = Relationship(back_populates="resultados")