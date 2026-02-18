from typing import List, Optional
from datetime import date
from sqlmodel import SQLModel

class SorteoBase(SQLModel):
    numero_sorteo: str
    fecha: date
    plan_id: int

class SorteoCreate(SorteoBase):
    pass

class SorteoRead(SorteoBase):
    id: int

class SorteoUpdate(SQLModel):
    numero_sorteo: Optional[str] = None
    fecha: Optional[date] = None
    plan_id: Optional[int] = None

# --- ESQUEMAS PARA CONSULTA PÚBLICA ---
class ResultadoPublico(SQLModel):
    id: Optional[int] = None
    premio_id: Optional[int] = None
    premio: str
    valor: str
    numero_ganador: Optional[str] = None

class SorteoPublicoRead(SQLModel):
    numero_sorteo: str
    fecha: date
    resultados: List[ResultadoPublico] = []