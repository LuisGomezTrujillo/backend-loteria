from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app import models
from app import schemas

router = APIRouter(prefix="/resultados", tags=["Resultados"])

@router.post("/", response_model=schemas.ResultadoRead)
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

@router.delete("/{sorteo_id}/{premio_id}")
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

@router.put("/{sorteo_id}/{premio_id}", response_model=schemas.ResultadoRead)
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
        raise HTTPException(status_code=400, detail="Faltan cifras.")

    resultado.numeros_ganadores = numeros_nuevos
    session.add(resultado)
    session.commit()
    session.refresh(resultado)
    return resultado