from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_roles
from app import models, schemas
from app.crud import crud_pre_sorteo as crud
from app.crud import crud_sorteo

router = APIRouter(prefix="/sorteos/{numero_sorteo}/presorteos", tags=["Pre-Sorteos"])

_LECTURA = (models.RolUsuario.admin, models.RolUsuario.operador, models.RolUsuario.consulta)
_ESCRITURA = (models.RolUsuario.admin, models.RolUsuario.operador)


def _obtener_sorteo_o_404(numero_sorteo: str, session: Session) -> models.Sorteo:
    sorteo = crud_sorteo.obtener_por_numero_sorteo(session, numero_sorteo)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo


@router.post("/", response_model=schemas.PreSorteoRead)
def crear_pre_sorteo(
    numero_sorteo: str,
    datos: schemas.PreSorteoCreate,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    try:
        return crud.crear_pre_sorteo(session, sorteo.id, datos.cantidad_balotas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.PreSorteoRead])
def listar_pre_sorteos(
    numero_sorteo: str,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_LECTURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    return crud.listar_pre_sorteos(session, sorteo.id)


@router.get("/{numero_prueba}", response_model=schemas.PreSorteoRead)
def obtener_pre_sorteo(
    numero_sorteo: str,
    numero_prueba: int,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_LECTURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    prueba = crud.obtener_pre_sorteo(session, sorteo.id, numero_prueba)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return prueba


@router.put("/{numero_prueba}", response_model=schemas.PreSorteoRead)
def guardar_resultado_prueba(
    numero_sorteo: str,
    numero_prueba: int,
    datos: schemas.PreSorteoUpdate,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    prueba = crud.obtener_pre_sorteo(session, sorteo.id, numero_prueba)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")

    if datos.numeros_ganadores is None:
        raise HTTPException(status_code=400, detail="Debes enviar numeros_ganadores.")

    try:
        return crud.guardar_resultado(session, prueba, datos.numeros_ganadores)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{numero_prueba}")
def eliminar_pre_sorteo(
    numero_sorteo: str,
    numero_prueba: int,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    prueba = crud.obtener_pre_sorteo(session, sorteo.id, numero_prueba)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    crud.eliminar_pre_sorteo(session, prueba)
    return {"ok": True, "message": f"Prueba {numero_prueba} del sorteo {numero_sorteo} eliminada."}