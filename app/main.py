from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import pytz
from datetime import datetime

from .database import create_db_and_tables, get_session
from . import models, schemas

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


# ==========================================
# --- ENDPOINTS DE PLANES ---
# ==========================================

@app.post("/planes/", response_model=schemas.PlanRead, tags=["Planes"])
def crear_plan(plan_in: schemas.PlanCreate, session: Session = Depends(get_session)):
    db_plan = models.PlanPremios(nombre=plan_in.nombre, descripcion=plan_in.descripcion)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)

    for premio_in in plan_in.premios:
        # ACTUALIZACIÓN PYDANTIC V2: dict() -> model_dump()
        db_premio = models.Premio(**premio_in.model_dump(), plan_id=db_plan.id)
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

# NUEVO ENDPOINT: Actualizar Plan
@app.put("/planes/{plan_id}", response_model=schemas.PlanRead, tags=["Planes"])
def actualizar_plan(plan_id: int, plan_in: schemas.PlanUpdate, session: Session = Depends(get_session)):
    plan_db = session.get(models.PlanPremios, plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # ACTUALIZACIÓN PYDANTIC V2: dict() -> model_dump()
    plan_data = plan_in.model_dump(exclude_unset=True)
    for key, value in plan_data.items():
        setattr(plan_db, key, value)
        
    session.add(plan_db)
    session.commit()
    session.refresh(plan_db)
    return plan_db

# NUEVO ENDPOINT: Eliminar Plan
@app.delete("/planes/{plan_id}", tags=["Planes"])
def eliminar_plan(plan_id: int, session: Session = Depends(get_session)):
    plan_db = session.get(models.PlanPremios, plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # Validación: No borrar si el plan ya está siendo usado en sorteos
    sorteos_asociados = session.exec(select(models.Sorteo).where(models.Sorteo.plan_id == plan_id)).first()
    if sorteos_asociados:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar este plan porque tiene sorteos históricos asociados."
        )

    try:
        # Borrar primero los premios asociados para mantener integridad (Cascade manual)
        premios_asociados = session.exec(select(models.Premio).where(models.Premio.plan_id == plan_id)).all()
        for premio in premios_asociados:
            session.delete(premio)
            
        session.delete(plan_db)
        session.commit()
        return {"ok": True, "message": f"Plan {plan_id} y sus premios eliminados."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==========================================
# --- ENDPOINTS DE SORTEOS ---
# ==========================================

@app.post("/sorteos/", response_model=schemas.SorteoRead, tags=["Sorteos"])
def crear_sorteo(sorteo_in: schemas.SorteoCreate, session: Session = Depends(get_session)):
    # ACTUALIZACIÓN PYDANTIC V2: from_orm() -> model_validate()
    db_sorteo = models.Sorteo.model_validate(sorteo_in)
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

@app.put("/sorteos/{sorteo_id}", response_model=schemas.SorteoRead, tags=["Sorteos"])
def actualizar_sorteo(sorteo_id: int, sorteo_in: schemas.SorteoUpdate, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
        
    # ACTUALIZACIÓN PYDANTIC V2: dict() -> model_dump()
    sorteo_data = sorteo_in.model_dump(exclude_unset=True)
    for key, value in sorteo_data.items():
        setattr(sorteo, key, value)
        
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo

@app.delete("/sorteos/{sorteo_id}/", tags=["Sorteos"])
def eliminar_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    db_sorteo = session.get(models.Sorteo, sorteo_id)
    if not db_sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    try:
        statement_res = select(models.Resultado).where(models.Resultado.sorteo_id == sorteo_id)
        resultados_asociados = session.exec(statement_res).all()
        for res in resultados_asociados:
            session.delete(res)

        session.delete(db_sorteo)
        session.commit()
        return {"ok": True, "message": f"Sorteo {sorteo_id} eliminado."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==========================================
# --- ENDPOINTS DE PREMIOS (CRUD INDIVIDUAL) ---
# ==========================================

# 1. ADICIONAR un premio a un plan existente
@app.post("/planes/{plan_id}/premios", response_model=schemas.PremioRead, tags=["Premios"])
def agregar_premio(plan_id: int, premio_in: schemas.PremioCreate, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Se crea el premio asignándole el plan_id directamente
    db_premio = models.Premio(**premio_in.model_dump(), plan_id=plan_id)
    session.add(db_premio)
    session.commit()
    session.refresh(db_premio)
    return db_premio

# 2. EDITAR un premio existente
@app.put("/premios/{premio_id}", response_model=schemas.PremioRead, tags=["Premios"])
def actualizar_premio(premio_id: int, premio_in: schemas.PremioUpdate, session: Session = Depends(get_session)):
    db_premio = session.get(models.Premio, premio_id)
    if not db_premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    
    premio_data = premio_in.model_dump(exclude_unset=True)
    for key, value in premio_data.items():
        setattr(db_premio, key, value)
        
    session.add(db_premio)
    session.commit()
    session.refresh(db_premio)
    return db_premio

# 3. ELIMINAR un premio existente
@app.delete("/premios/{premio_id}", tags=["Premios"])
def eliminar_premio(premio_id: int, session: Session = Depends(get_session)):
    db_premio = session.get(models.Premio, premio_id)
    if not db_premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
        
    # VALIDACIÓN DE SEGURIDAD: No borrar si ya hay ganadores registrados
    resultados_asociados = session.exec(select(models.Resultado).where(models.Resultado.premio_id == premio_id)).first()
    if resultados_asociados:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar este premio porque ya tiene resultados registrados en un sorteo."
        )
        
    try:
        session.delete(db_premio)
        session.commit()
        return {"ok": True, "message": "Premio eliminado exitosamente"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==========================================
# --- ENDPOINT DE RESULTADOS ---
# ==========================================

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
        raise HTTPException(status_code=400, detail=f"Faltan cifras. Se esperan {premio.cantidad_balotas}")

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
def consultar_resultados_publico(numero_sorteo: str, session: Session = Depends(get_session)):
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
            id=res.id,              
            premio_id=prem.id,      
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
        raise HTTPException(status_code=400, detail=f"Faltan cifras.")

    resultado.numeros_ganadores = numeros_nuevos
    session.add(resultado)
    session.commit()
    session.refresh(resultado)
    return resultado