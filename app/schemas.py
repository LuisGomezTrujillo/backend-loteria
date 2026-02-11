from typing import List, Optional
from datetime import date
from sqlmodel import SQLModel


# --- SCHEMAS DE PREMIO ---
class PremioBase(SQLModel):
    titulo: str
    valor: str
    cantidad_balotas: int

class PremioCreate(PremioBase):
    pass

class PremioRead(PremioBase):
    id: int
    plan_id: int


# --- SCHEMAS DE PLAN DE PREMIOS ---
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


# --- SCHEMAS DE SORTEO ---
class SorteoBase(SQLModel):
    numero_sorteo: int
    fecha: date
    plan_id: int

class SorteoCreate(SorteoBase):
    pass

class SorteoRead(SorteoBase):
    id: int

class SorteoUpdate(SQLModel):
    numero_sorteo: Optional[int] = None
    fecha: Optional[date] = None
    plan_id: Optional[int] = None


# --- SCHEMAS DE RESULTADO ---
class ResultadoCreate(SQLModel):
    sorteo_id: int
    premio_titulo: str
    numeros_ganadores: str

class ResultadoRead(SQLModel):
    id: int
    sorteo_id: int
    premio_id: int
    numeros_ganadores: str


# --- CONSULTA PÚBLICA ---
class ResultadoPublico(SQLModel):
    premio: str
    valor: str
    # ✅ FIX: Optional porque un sorteo puede no tener resultados aún
    # El frontend ya maneja null con el placeholder "----"
    numero_ganador: Optional[str] = None

class SorteoPublicoRead(SQLModel):
    numero_sorteo: int
    fecha: date
    resultados: List[ResultadoPublico] = []