from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List

from database import create_db_and_tables, get_session
from models import Sorteo

app = FastAPI(
    title="API Sorteos Lotería de Manizales",
    description="Backend para registrar resultados de sorteos desde Smart TV"
)

# --- Configuración de CORS ---
# Esto permite que tu frontend en React se comunique con este backend
origins = [
    "*", # En producción, idealmente cambias esto por la URL de tu frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Evento de Inicio ---
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"mensaje": "API de Lotería funcionando correctamente 🚀"}

@app.post("/resultados/", response_model=Sorteo)
def crear_resultado(sorteo: Sorteo, session: Session = Depends(get_session)):
    """
    Recibe el resultado desde el TV y lo guarda en la base de datos.
    """
    try:
        session.add(sorteo)
        session.commit()
        session.refresh(sorteo)
        return sorteo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resultados/", response_model=List[Sorteo])
def leer_resultados(offset: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """
    Lista los resultados guardados (útil para verificar).
    """
    resultados = session.exec(select(Sorteo).offset(offset).limit(limit)).all()
    return resultados