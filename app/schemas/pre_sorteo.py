from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel
from pydantic import field_validator

CANTIDADES_BALOTAS_VALIDAS = {4, 6}


class PreSorteoCreate(SQLModel):
    # 6 -> 7 cifras (como el Premio Mayor). 4 -> 4 cifras (como los premios secos).
    cantidad_balotas: int = 6

    @field_validator("cantidad_balotas")
    @classmethod
    def validar_cantidad_balotas(cls, v: int) -> int:
        if v not in CANTIDADES_BALOTAS_VALIDAS:
            raise ValueError("cantidad_balotas debe ser 4 o 6.")
        return v


class PreSorteoUpdate(SQLModel):
    numeros_ganadores: Optional[str] = None


class PreSorteoRead(SQLModel):
    id: int
    sorteo_id: int
    numero_prueba: int
    cantidad_balotas: int
    numeros_ganadores: Optional[str] = None
    fecha_hora: Optional[datetime] = None