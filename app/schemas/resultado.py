from sqlmodel import SQLModel

class ResultadoCreate(SQLModel):
    sorteo_id: int
    premio_titulo: str
    numeros_ganadores: str

class ResultadoRead(SQLModel):
    id: int
    sorteo_id: int
    premio_id: int
    numeros_ganadores: str