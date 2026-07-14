from typing import List, Optional
from sqlmodel import Session, select

from app import models, schemas


def obtener_por_numero_sorteo(session: Session, numero_sorteo: str) -> Optional[models.Sorteo]:
    """Busca un sorteo por su código/número (string), NO por el id interno."""
    statement = select(models.Sorteo).where(models.Sorteo.numero_sorteo == numero_sorteo)
    return session.exec(statement).first()


def obtener_por_id(session: Session, sorteo_id: int) -> Optional[models.Sorteo]:
    return session.get(models.Sorteo, sorteo_id)


def listar_sorteos(session: Session) -> List[models.Sorteo]:
    return session.exec(select(models.Sorteo)).all()


def crear_sorteo(session: Session, data: schemas.SorteoCreate) -> models.Sorteo:
    db_sorteo = models.Sorteo.model_validate(data)
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo


def actualizar_sorteo(
    session: Session, db_sorteo: models.Sorteo, data: schemas.SorteoUpdate
) -> models.Sorteo:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sorteo, key, value)
    session.add(db_sorteo)
    session.commit()
    session.refresh(db_sorteo)
    return db_sorteo


def eliminar_sorteo(session: Session, db_sorteo: models.Sorteo) -> None:
    session.delete(db_sorteo)
    session.commit()