from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos la configuración de DB y los routers
from app.core.database import create_db_and_tables
from app.api import (
    routes_planes,
    routes_premios,
    routes_sorteos,
    routes_resultados,
    routes_tubos,
    routes_pre_sorteos,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Lotería de Manizales API", lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
# NOTA: el regex acepta http:// o https:// para localhost (desarrollo usa
# http), y solo https:// para el dominio de Vercel (producción).
app.add_middleware(
    CORSMiddleware,
 #   allow_origin_regex=r"https?://(localhost:3000|frontend-risaralda(-git-[\w-]+-[\w]+)?\.vercel\.app)",
    allow_origin_regex=r"https?://(localhost:3000|frontend-loteria(-git-[\w-]+-[\w]+)?\.vercel\.app)",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- INCLUSIÓN DE ROUTERS ---
app.include_router(routes_planes.router)
app.include_router(routes_premios.router)
app.include_router(routes_sorteos.router)
app.include_router(routes_resultados.router)
app.include_router(routes_tubos.router)
app.include_router(routes_pre_sorteos.router)  # <--- Nuevo router de pre-sorteos

# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# # Importamos la configuración de DB y los routers
# from app.core.database import create_db_and_tables
# from app.api import routes_planes, routes_premios, routes_sorteos, routes_resultados, routes_tubos

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     create_db_and_tables()
#     yield

# app = FastAPI(title="Lotería de Manizales API", lifespan=lifespan)

# # --- CONFIGURACIÓN CORS ---
# # NOTA: el regex acepta http:// o https:// para localhost (desarrollo usa
# # http), y solo https:// para el dominio de Vercel (producción).
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=r"https?://(localhost:3000|frontend-loteria(-git-[\w-]+-[\w]+)?\.vercel\.app)",
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # --- INCLUSIÓN DE ROUTERS ---
# app.include_router(routes_planes.router)
# app.include_router(routes_premios.router)  # <--- Nuevo router incluido
# app.include_router(routes_sorteos.router)
# app.include_router(routes_resultados.router)
# app.include_router(routes_tubos.router)  # <--- Nuevo router incluido