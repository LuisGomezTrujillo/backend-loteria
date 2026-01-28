from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Sorteo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero_sorteo: str
    fecha: datetime = Field(default_factory=datetime.now)
    titulo_premio: str  # Ej: "MAYOR", "SECO 36"
    resultado_concatenado: str # Ej: "123456" (los 6 inputs unidos)
    
    # Campos opcionales para auditoría
    inputs_usados: int # Para saber si fue de 4 o 6 cifras