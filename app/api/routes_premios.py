from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app import models
from app import schemas

router = APIRouter(tags=["Premios"])

@router.post("/planes/{plan_id}/premios", response_model=schemas.PremioRead)
def agregar_premio(plan_id: int, premio_in: schemas.PremioCreate, session: Session = Depends(get_session)):
    plan = session.get(models.PlanPremios, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    db_premio = models.Premio(**premio_in.model_dump(), plan_id=plan_id)
    session.add(db_premio)
    session.commit()
    session.refresh(db_premio)
    return db_premio

@router.put("/premios/{premio_id}", response_model=schemas.PremioRead)
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

@router.delete("/premios/{premio_id}")
def eliminar_premio(premio_id: int, session: Session = Depends(get_session)):
    db_premio = session.get(models.Premio, premio_id)
    if not db_premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
        
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