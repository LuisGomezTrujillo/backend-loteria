from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List
# 1. IMPORTAR EL MIDDLEWARE (NUEVO)
from fastapi.middleware.cors import CORSMiddleware 

from .database import create_db_and_tables, get_session
from . import models, schemas

app = FastAPI(title="Lotería de Manizales API")

# 2. CONFIGURAR LOS ORÍGENES PERMITIDOS (NUEVO)
origins = [
    "http://localhost:3000",    # React local
    "http://127.0.0.1:3000",    # React local (alternativa IP)
    # Aquí agregarás la URL de tu frontend en Render cuando despliegues
    # "https://tu-frontend-en-render.com"
]

# 3. AÑADIR EL MIDDLEWARE A LA APP (NUEVO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],         # Permitir todos los métodos (GET, POST, PATCH, DELETE, OPTIONS)
    allow_headers=["*"],         # Permitir todos los headers
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ... (El resto de tu código sigue igual: endpoints de planes, sorteos, etc.)

# ==========================================
# CRUD: PLANES DE PREMIOS
# ==========================================

@app.post("/planes/", response_model=schemas.PlanRead, tags=["Planes"])
def crear_plan(plan_in: schemas.PlanCreate, session: Session = Depends(get_session)):
    db_plan = models.PlanPremios(nombre=plan_in.nombre, descripcion=plan_in.descripcion)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    
    for premio_in in plan_in.premios:
        db_premio = models.Premio(
            plan_id=db_plan.id,
            titulo=premio_in.titulo,
            valor=premio_in.valor,
            cantidad_balotas=premio_in.cantidad_balotas
        )
        session.add(db_premio)
    
    session.commit()
    session.refresh(db_plan)
    return db_plan

@app.get("/planes/", response_model=List[schemas.PlanRead], tags=["Planes"])
def listar_planes(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    plan_query = select(models.PlanPremios).offset(offset).limit(limit)
    planes = session.exec(plan_query).all()
    return planes

@app.get("/planes/{plan_id}", response_model=schemas.PlanRead, tags=["Planes"])
def obtener_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan

@app.patch("/planes/{plan_id}", response_model=schemas.PlanRead, tags=["Planes"])
def actualizar_plan(plan_id: int, plan_update: schemas.PlanUpdate, session: Session = Depends(get_session)):
    db_plan = session.get(models.PlanPremios, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Lógica de actualización parcial
    plan_data = plan_update.dict(exclude_unset=True)
    for key, value in plan_data.items():
        setattr(db_plan, key, value)
        
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return db_plan

@app.delete("/planes/{plan_id}", tags=["Planes"])
def eliminar_plan(plan_id: int, session: Session = Depends(get_session)):
    db_plan = session.get(models.PlanPremios, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Nota: Si hay sorteos o premios ligados, esto podría fallar dependiendo de la configuración de cascada en SQL.
    # Por defecto en SQLModel/SQLAlchemy hay que borrar los hijos manualmente o configurar cascade delete.
    # Aquí borramos el plan, asumiendo una gestión simple.
    
    session.delete(db_plan)
    session.commit()
    return {"ok": True, "message": "Plan eliminado correctamente"}


# ==========================================
# CRUD: SORTEOS
# ==========================================

@app.post("/sorteos/", response_model=schemas.SorteoRead, tags=["Sorteos"])
def crear_sorteo(sorteo_in: schemas.SorteoCreate, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, sorteo_in.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="El Plan de Premios especificado no existe")
        
    db_sorteo = models.Sorteo.from_orm(sorteo_in)
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo

@app.get("/sorteos/", response_model=List[schemas.SorteoRead], tags=["Sorteos"])
def listar_sorteos(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    sorteos = session.exec(select(models.Sorteo).offset(offset).limit(limit)).all()
    return sorteos

@app.get("/sorteos/{sorteo_id}", response_model=schemas.SorteoRead, tags=["Sorteos"])
def obtener_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo

@app.patch("/sorteos/{sorteo_id}", response_model=schemas.SorteoRead, tags=["Sorteos"])
def actualizar_sorteo(sorteo_id: int, sorteo_update: schemas.SorteoUpdate, session: Session = Depends(get_session)):
    db_sorteo = session.get(models.Sorteo, sorteo_id)
    if not db_sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    
    sorteo_data = sorteo_update.dict(exclude_unset=True)
    for key, value in sorteo_data.items():
        setattr(db_sorteo, key, value)
        
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo

@app.delete("/sorteos/{sorteo_id}", tags=["Sorteos"])
def eliminar_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    db_sorteo = session.get(models.Sorteo, sorteo_id)
    if not db_sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    
    session.delete(db_sorteo)
    session.commit()
    return {"ok": True, "message": "Sorteo eliminado correctamente"}


# ==========================================
# RESULTADOS (Mantenemos lo previo)
# ==========================================

@app.post("/sorteos/{sorteo_id}/resultados/", response_model=schemas.ResultadoRead, tags=["Resultados"])
def registrar_resultado(
    sorteo_id: int, 
    resultado_in: schemas.ResultadoCreate, 
    session: Session = Depends(get_session)
):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    
    premio = session.get(models.Premio, resultado_in.premio_id)
    if not premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    
    if len(resultado_in.numeros_ganadores) != premio.cantidad_balotas+1:
         raise HTTPException(
             status_code=400, 
             detail=f"El premio '{premio.titulo}' requiere exactamente {premio.cantidad_balotas+1} cifras."
         )

    db_resultado = models.Resultado(
        sorteo_id=sorteo_id,
        premio_id=resultado_in.premio_id,
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

    query = select(models.Resultado, models.Premio)\
            .where(models.Resultado.sorteo_id == sorteo.id)\
            .join(models.Premio)
            
    data = session.exec(query).all()
    
    lista_resultados = []
    for res, prem in data:
        lista_resultados.append(schemas.ResultadoPublico(
            premio=prem.titulo,
            valor=prem.valor,
            numero_ganador=res.numeros_ganadores
        ))
        
    return schemas.SorteoPublicoRead(
        sorteo=sorteo.numero_sorteo,
        fecha=sorteo.fecha,
        resultados=lista_resultados
    )

# uvicorn main:app --host 0.0.0.0 --port 10000
# uvicorn main:app
