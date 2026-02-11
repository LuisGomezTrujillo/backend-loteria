from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List
from fastapi.middleware.cors import CORSMiddleware 

# Asegúrate de que las importaciones relativas funcionen según tu estructura de carpetas
from .database import create_db_and_tables, get_session
from . import models, schemas

app = FastAPI(title="Lotería de Manizales API")


origins = [
    "https://frontend-loteria.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Lista explícita
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
    if not plan: raise HTTPException(status_code=404, detail="Plan no encontrado")
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
    if not sorteo: raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo

# --- ENDPOINT DE RESULTADOS (CORREGIDO) ---
@app.post("/resultados/", response_model=schemas.ResultadoRead, tags=["Resultados"])
def crear_resultado(resultado_in: schemas.ResultadoCreate, session: Session = Depends(get_session)):
    # 1. Buscar el sorteo para obtener el plan_id
    sorteo = session.get(models.Sorteo, resultado_in.sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    # 2. Buscar el premio por título dentro de ese plan
    statement = select(models.Premio).where(
        models.Premio.plan_id == sorteo.plan_id,
        models.Premio.titulo == resultado_in.premio_titulo
    )
    premio = session.exec(statement).first()
    
    if not premio:
        raise HTTPException(status_code=404, detail=f"Premio '{resultado_in.premio_titulo}' no existe")

    # 3. Validar longitud (CORRECCIÓN APLICADA)
    # Se cambió la validación estricta (!=) por una validación de mínimo (<).
    # Esto permite que si la BD dice 4 balotas, pero enviamos 7 (4 numero + 3 serie), lo acepte.
    if len(resultado_in.numeros_ganadores) < premio.cantidad_balotas:
         raise HTTPException(status_code=400, detail=f"Faltan cifras. Se esperan al menos {premio.cantidad_balotas}")

    # 4. Crear registro
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
    if not sorteo: raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    query = select(models.Resultado, models.Premio)\
            .where(models.Resultado.sorteo_id == sorteo.id)\
            .join(models.Premio)
    data = session.exec(query).all()
    
    lista_resultados = [
        schemas.ResultadoPublico(
            premio=prem.titulo,
            valor=prem.valor,
            numero_ganador=res.numeros_ganadores
        ) for res, prem in data
    ]
    return schemas.SorteoPublicoRead(numero_sorteo=sorteo.numero_sorteo, fecha=sorteo.fecha, resultados=lista_resultados)

# ... (Manten todo el código anterior hasta los endpoints de resultados)

# --- NUEVOS ENDPOINTS PARA CRUD (Editar / Borrar) ---

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
def actualizar_resultado(sorteo_id: int, premio_id: int, numeros_nuevos: str, session: Session = Depends(get_session)):
    # 1. Buscar el resultado existente
    statement = select(models.Resultado).where(
        models.Resultado.sorteo_id == sorteo_id,
        models.Resultado.premio_id == premio_id
    )
    resultado = session.exec(statement).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado para editar")

    # 2. Validar longitud con el premio
    premio = session.get(models.Premio, premio_id)
    if len(numeros_nuevos) < premio.cantidad_balotas:
         raise HTTPException(status_code=400, detail=f"Faltan cifras. Se esperan al menos {premio.cantidad_balotas}")

    # 3. Actualizar
    resultado.numeros_ganadores = numeros_nuevos
    session.add(resultado)
    session.commit()
    session.refresh(resultado)
    return resultado
