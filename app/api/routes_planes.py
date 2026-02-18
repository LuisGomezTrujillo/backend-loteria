from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List

from app.core.database import get_session
from app import models
from app import schemas

router = APIRouter(prefix="/planes", tags=["Planes"])

@router.post("/", response_model=schemas.PlanRead)
def crear_plan(plan_in: schemas.PlanCreate, session: Session = Depends(get_session)):
    db_plan = models.PlanPremios(nombre=plan_in.nombre, descripcion=plan_in.descripcion)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)

    for premio_in in plan_in.premios:
        db_premio = models.Premio(**premio_in.model_dump(), plan_id=db_plan.id)
        session.add(db_premio)

    session.commit()
    session.refresh(db_plan)
    return db_plan

@router.get("/", response_model=List[schemas.PlanRead])
def listar_planes(session: Session = Depends(get_session)):
    return session.exec(select(models.PlanPremios)).all()

@router.get("/{plan_id}", response_model=schemas.PlanRead)
def obtener_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan

@router.put("/{plan_id}", response_model=schemas.PlanRead)
def actualizar_plan(plan_id: int, plan_in: schemas.PlanUpdate, session: Session = Depends(get_session)):
    plan_db = session.get(models.PlanPremios, plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    plan_data = plan_in.model_dump(exclude_unset=True)
    for key, value in plan_data.items():
        setattr(plan_db, key, value)
        
    session.add(plan_db)
    session.commit()
    session.refresh(plan_db)
    return plan_db

@router.delete("/{plan_id}")
def eliminar_plan(plan_id: int, session: Session = Depends(get_session)):
    plan_db = session.get(models.PlanPremios, plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    sorteos_asociados = session.exec(select(models.Sorteo).where(models.Sorteo.plan_id == plan_id)).first()
    if sorteos_asociados:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar este plan porque tiene sorteos históricos asociados."
        )

    try:
        premios_asociados = session.exec(select(models.Premio).where(models.Premio.plan_id == plan_id)).all()
        for premio in premios_asociados:
            session.delete(premio)
            
        session.delete(plan_db)
        session.commit()
        return {"ok": True, "message": f"Plan {plan_id} y sus premios eliminados."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")