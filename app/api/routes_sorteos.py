from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List

from app.core.database import get_session
from app import models
from app import schemas

router = APIRouter(prefix="/sorteos", tags=["Sorteos"])

@router.post("/", response_model=schemas.SorteoRead)
def crear_sorteo(sorteo_in: schemas.SorteoCreate, session: Session = Depends(get_session)):
    db_sorteo = models.Sorteo.model_validate(sorteo_in)
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo

@router.get("/", response_model=List[schemas.SorteoRead])
def listar_sorteos(session: Session = Depends(get_session)):
    return session.exec(select(models.Sorteo)).all()

@router.get("/{sorteo_id}", response_model=schemas.SorteoRead)
def obtener_sorteo(sorteo_id: int, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo

@router.put("/{sorteo_id}", response_model=schemas.SorteoRead)
def actualizar_sorteo(sorteo_id: int, sorteo_in: schemas.SorteoUpdate, session: Session = Depends(get_session)):
    sorteo = session.get(models.Sorteo, sorteo_id)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
        
    sorteo_data = sorteo_in.model_dump(exclude_unset=True)
    for key, value in sorteo_data.items():
        setattr(sorteo, key, value)
        
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo

@router.delete("/{sorteo_id}")
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

# --- CONSULTA PÚBLICA ---
@router.get("/{numero_sorteo}/publico", response_model=schemas.SorteoPublicoRead, tags=["Consulta Pública"])
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