from typing import Optional
from sqlmodel import Session, select

from app import models, schemas
from app.schemas.tubo import TuboBase


def obtener_por_sorteo(session: Session, sorteo_id: int) -> Optional[models.Tubo]:
    statement = select(models.Tubo).where(models.Tubo.sorteo_id == sorteo_id)
    return session.exec(statement).first()


def crear_configuracion(
    session: Session, sorteo_id: int, data: schemas.TuboCreate
) -> models.Tubo:
    db_config = models.Tubo(
        sorteo_id=sorteo_id,
        **data.model_dump(),
    )
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


def actualizar_configuracion(
    session: Session,
    db_config: models.Tubo,
    data: schemas.TuboUpdate,
) -> models.Tubo:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)

    # Revalidamos el registro completo (rango + unicidad de tubos) ya con
    # los cambios fusionados, para no permitir un PUT parcial inválido.
    TuboBase.model_validate(
        {
            "tubo_urna1": db_config.tubo_urna1,
            "tubo_urna2": db_config.tubo_urna2,
            "tubo_urna3": db_config.tubo_urna3,
            "tubo_urna4": db_config.tubo_urna4,
            "tubos_urna5": db_config.tubos_urna5,
            "tubo_urna6": db_config.tubo_urna6,
        }
    )

    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


def eliminar_configuracion(session: Session, db_config: models.Tubo) -> None:
    session.delete(db_config)
    session.commit()