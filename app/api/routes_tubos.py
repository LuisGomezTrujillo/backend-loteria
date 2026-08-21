from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from pydantic import ValidationError

from app.core.database import get_session
from app.core.deps import require_roles
from app import models, schemas
from app.crud import crud_tubo as crud
from app.crud import crud_sorteo

# El identificador en la URL ahora es el numero_sorteo (string, ej. "1234"),
# NO el id interno de la base de datos.
router = APIRouter(prefix="/sorteos/{numero_sorteo}/tubos", tags=["Balotas de tubos en urnas"])

_LECTURA = (models.RolUsuario.admin, models.RolUsuario.operador, models.RolUsuario.consulta)
_ESCRITURA = (models.RolUsuario.admin, models.RolUsuario.operador)


def _obtener_sorteo_o_404(numero_sorteo: str, session: Session) -> models.Sorteo:
    sorteo = crud_sorteo.obtener_por_numero_sorteo(session, numero_sorteo)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return sorteo


@router.post("/", response_model=schemas.TuboRead)
def crear_tubos(
    numero_sorteo: str,
    config_in: schemas.TuboCreate,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)

    if crud.obtener_por_sorteo(session, sorteo.id):
        raise HTTPException(
            status_code=400,
            detail="Este sorteo ya tiene una configuración de tubos registrada. Use PUT para modificarla.",
        )

    try:
        return crud.crear_configuracion(session, sorteo.id, config_in)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/", response_model=schemas.TuboRead)
def obtener_configuracion_tubos(
    numero_sorteo: str,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_LECTURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    config = crud.obtener_por_sorteo(session, sorteo.id)
    if not config:
        raise HTTPException(status_code=404, detail="Este sorteo no tiene configuración de tubos registrada.")
    return config


@router.put("/", response_model=schemas.TuboRead)
def actualizar_configuracion_tubos(
    numero_sorteo: str,
    config_in: schemas.TuboUpdate,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    config = crud.obtener_por_sorteo(session, sorteo.id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Este sorteo no tiene configuración de tubos registrada. Use POST para crearla.",
        )

    try:
        return crud.actualizar_configuracion(session, config, config_in)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/")
def eliminar_configuracion_tubos(
    numero_sorteo: str,
    session: Session = Depends(get_session),
    _: models.Usuario = Depends(require_roles(*_ESCRITURA)),
):
    sorteo = _obtener_sorteo_o_404(numero_sorteo, session)
    config = crud.obtener_por_sorteo(session, sorteo.id)
    if not config:
        raise HTTPException(status_code=404, detail="Este sorteo no tiene configuración de tubos registrada.")
    crud.eliminar_configuracion(session, config)
    return {"ok": True, "message": f"Configuración de tubos del sorteo {numero_sorteo} eliminada."}