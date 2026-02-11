from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables, get_session
from . import models, schemas


# ✅ FIX 1: Usar 'lifespan' en lugar del deprecado @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Lotería de Manizales API", lifespan=lifespan)


# ✅ FIX 2: CORS robusto — acepta tu dominio de Vercel y cualquier preview/rama
# Cambia "frontend-loteria" por el nombre real de tu proyecto en Vercel si es diferente
# --- CONFIGURACIÓN CORS BLINDADA ---
origins = [
    "http://localhost:3000",
    "https://frontend-loteria.vercel.app" # <--- Tu URL de Vercel SIN barra al final
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ENDPOINTS DE PLANES ---

@app.post("/planes/", response_model=schemas.PlanRead, tags=["Planes"])
def crear_plan(plan_in: schemas.PlanCreate, session: Session = Depends(get_session)):
    db_plan = models.PlanPremios(nombre=plan_in.nombre, descripcion=plan_in.descripcion)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)

    for premio_in in plan_in.premios:
        db_premio = models.Premio(**premio_in.dict(), plan_id=db_plan.id)
        session.add(db_premio)

    session.commit()
    session.refresh(db_plan)
    return db_plan

@app.get("/planes/", response_model=List[schemas.PlanRead], tags=["Planes"])
def listar_planes(session: Session = Depends(get_session)):
    return session.exec(select(models.PlanPremios)).all()

@app.get("/planes/{plan_id}", response_model=schemas.PlanRead, tags=["Planes"])
def obtener_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


# --- ENDPOINTS DE SORTEOS ---

@app.post("/sorteos/", response_model=schemas.SorteoRead, tags=["Sorteos"])
def crear_sorteo(sorteo_in: schemas.SorteoCreate, session: Session = Depends(get_session)):
    db_sorteo = models.Sorteo.from_orm(sorteo_in)
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo

@app.get("/sorteos/", response_model=List[schemas.SorteoRead], tags=["Sorteos"])
def listar_sorteos(session: Session = Depends(get_session)):
    return session.exec(select(models.Sorteo)).all()

@app.get("/sorteos/{sorteo_id}", response_model=schemas.SorteoRead, tags=["Sorteos"])
def obtener_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo

# ✅ FIX 3: Endpoint PUT que faltaba — ManageSorteo.js lo llama pero no existía
@app.put("/sorteos/{sorteo_id}", response_model=schemas.SorteoRead, tags=["Sorteos"])
def actualizar_sorteo(sorteo_id: int, sorteo_in: schemas.SorteoCreate, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    sorteo_data = sorteo_in.dict(exclude_unset=True)
    for key, value in sorteo_data.items():
        setattr(sorteo, key, value)
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo

@app.delete("/sorteos/{sorteo_id}", tags=["Sorteos"])
def eliminar_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    session.delete(sorteo)
    session.commit()
    return {"ok": True, "message": "Sorteo eliminado"}


# --- ENDPOINT DE RESULTADOS ---

@app.post("/resultados/", response_model=schemas.ResultadoRead, tags=["Resultados"])
def crear_resultado(resultado_in: schemas.ResultadoCreate, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, resultado_in.sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    statement = select(models.Premio).where(
        models.Premio.plan_id == sorteo.plan_id,
        models.Premio.titulo == resultado_in.premio_titulo
    )
    premio = session.exec(statement).first()

    if not premio:
        raise HTTPException(status_code=404, detail=f"Premio '{resultado_in.premio_titulo}' no existe")

    if len(resultado_in.numeros_ganadores) < premio.cantidad_balotas:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan cifras. Se esperan al menos {premio.cantidad_balotas}"
        )

    db_resultado = models.Resultado(
        sorteo_id=resultado_in.sorteo_id,
        premio_id=premio.id,
        numeros_ganadores=resultado_in.numeros_ganadores
    )
    session.add(db_resultado)
    session.commit()
    session.refresh(db_resultado)
    return db_resultado

@app.get("/sorteos/{numero_sorteo}/publico", response_model=schemas.SorteoPublicoRead, tags=["Consulta Pública"])
def consultar_resultados_publico(numero_sorteo: int, session: Session = Depends(get_session)):
    statement = select(models.Sorteo).where(models.Sorteo.numero_sorteo == numero_sorteo)
    sorteo = session.exec(statement).first()
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    query = (
        select(models.Resultado, models.Premio)
        .where(models.Resultado.sorteo_id == sorteo.id)
        .join(models.Premio)
    )
    data = session.exec(query).all()

    lista_resultados = [
        schemas.ResultadoPublico(
            premio=prem.titulo,
            valor=prem.valor,
            numero_ganador=res.numeros_ganadores
        )
        for res, prem in data
    ]
    return schemas.SorteoPublicoRead(
        numero_sorteo=sorteo.numero_sorteo,
        fecha=sorteo.fecha,
        resultados=lista_resultados
    )

@app.delete("/resultados/{sorteo_id}/{premio_id}", tags=["Resultados"])
def eliminar_resultado(sorteo_id: int, premio_id: int, session: Session = Depends(get_session)):
    statement = select(models.Resultado).where(
        models.Resultado.sorteo_id == sorteo_id,
        models.Resultado.premio_id == premio_id
    )
    resultado = session.exec(statement).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    session.delete(resultado)
    session.commit()
    return {"ok": True, "message": "Resultado eliminado"}

@app.put("/resultados/{sorteo_id}/{premio_id}", response_model=schemas.ResultadoRead, tags=["Resultados"])
def actualizar_resultado(
    sorteo_id: int,
    premio_id: int,
    numeros_nuevos: str = Query(...),
    session: Session = Depends(get_session)
):
    statement = select(models.Resultado).where(
        models.Resultado.sorteo_id == sorteo_id,
        models.Resultado.premio_id == premio_id
    )
    resultado = session.exec(statement).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado para editar")

    premio = session.get(models.Premio, premio_id)
    if len(numeros_nuevos) < premio.cantidad_balotas:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan cifras. Se esperan al menos {premio.cantidad_balotas}"
        )

    resultado.numeros_ganadores = numeros_nuevos
    session.add(resultado)
    session.commit()
    session.refresh(resultado)
    return resultado