from typing import Optional
from sqlmodel import SQLModel
from pydantic import field_validator, model_validator

# Rango válido para tubos individuales (urnas 1-4 y 6)
TUBO_MIN = 1
TUBO_MAX = 17

# Conjuntos válidos para la urna 5
TUBOS_URNA5_VALIDOS = {"18-19-20", "21-22-23", "24-25-26"}


class TuboBase(SQLModel):
    tubo_urna1: str
    tubo_urna2: str
    tubo_urna3: str
    tubo_urna4: str
    tubos_urna5: str
    tubo_urna6: str

    @field_validator("tubo_urna1", "tubo_urna2", "tubo_urna3", "tubo_urna4", "tubo_urna6")
    @classmethod
    def validar_rango_tubo(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El tubo debe ser un número (texto) entre 1 y 17.")
        numero = int(v)
        if not (TUBO_MIN <= numero <= TUBO_MAX):
            raise ValueError(f"El tubo debe estar entre {TUBO_MIN} y {TUBO_MAX}.")
        # Normaliza (quita espacios y ceros a la izquierda, ej. " 07" -> "7")
        return str(numero)

    @field_validator("tubos_urna5")
    @classmethod
    def validar_tubos_urna5(cls, v: str) -> str:
        if v not in TUBOS_URNA5_VALIDOS:
            opciones = ", ".join(sorted(TUBOS_URNA5_VALIDOS))
            raise ValueError(f"tubos_urna5 debe ser uno de: {opciones}")
        return v

    @model_validator(mode="after")
    def validar_tubos_no_repetidos(self):
        tubos = [self.tubo_urna1, self.tubo_urna2, self.tubo_urna3, self.tubo_urna4, self.tubo_urna6]
        if len(set(tubos)) != len(tubos):
            raise ValueError(
                "Los tubos de las urnas 1, 2, 3, 4 y 6 deben ser distintos entre sí "
                "(no se puede repetir un mismo tubo)."
            )
        return self


# NOTA: ya NO incluye sorteo_id. El sorteo se identifica por numero_sorteo
# en la URL (/sorteos/{numero_sorteo}/tubos), y el backend resuelve el id
# internamente antes de guardar.
class TuboCreate(TuboBase):
    pass


class TuboRead(TuboBase):
    id: int          # <-- corregido: antes decía "str", debía ser "int"
    sorteo_id: int


class TuboUpdate(SQLModel):
    tubo_urna1: Optional[str] = None
    tubo_urna2: Optional[str] = None
    tubo_urna3: Optional[str] = None
    tubo_urna4: Optional[str] = None
    tubos_urna5: Optional[str] = None
    tubo_urna6: Optional[str] = None

    @field_validator("tubo_urna1", "tubo_urna2", "tubo_urna3", "tubo_urna4", "tubo_urna6")
    @classmethod
    def validar_rango_tubo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El tubo debe ser un número (texto) entre 1 y 17.")
        numero = int(v)
        if not (TUBO_MIN <= numero <= TUBO_MAX):
            raise ValueError(f"El tubo debe estar entre {TUBO_MIN} y {TUBO_MAX}.")
        return str(numero)

    @field_validator("tubos_urna5")
    @classmethod
    def validar_tubos_urna5(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in TUBOS_URNA5_VALIDOS:
            opciones = ", ".join(sorted(TUBOS_URNA5_VALIDOS))
            raise ValueError(f"tubos_urna5 debe ser uno de: {opciones}")
        return v