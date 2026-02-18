from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos la configuración de DB y los routers
from app.core.database import create_db_and_tables
from app.api import routes_planes, routes_premios, routes_sorteos, routes_resultados

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Lotería de Manizales API", lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
origins = [
    "http://localhost:3000",
    "https://frontend-loteria.vercel.app", 
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUSIÓN DE ROUTERS ---
app.include_router(routes_planes.router)
app.include_router(routes_premios.router)  # <--- Nuevo router incluido
app.include_router(routes_sorteos.router)
app.include_router(routes_resultados.router)