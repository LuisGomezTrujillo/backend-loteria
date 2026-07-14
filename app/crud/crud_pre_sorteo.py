from typing import List, Optional
from sqlmodel import Session, select

from app import models

MAX_PRUEBAS_POR_SORTEO = 10


def obtener_siguiente_numero_prueba(session: Session, sorteo_id: int) -> int:
    statement = select(models.PreSorteo).where(models.PreSorteo.sorteo_id == sorteo_id)
    pruebas = session.exec(statement).all()
    if not pruebas:
        return 1
    return max(p.numero_prueba for p in pruebas) + 1


def crear_pre_sorteo(session: Session, sorteo_id: int, cantidad_balotas: int = 6) -> models.PreSorteo:
    numero_prueba = obtener_siguiente_numero_prueba(session, sorteo_id)
    if numero_prueba > MAX_PRUEBAS_POR_SORTEO:
        raise ValueError(
            f"Ya se registraron {MAX_PRUEBAS_POR_SORTEO} pruebas para este sorteo (máximo permitido)."
        )

    db_prueba = models.PreSorteo(
        sorteo_id=sorteo_id,
        numero_prueba=numero_prueba,
        cantidad_balotas=cantidad_balotas,
    )
    session.add(db_prueba)
    session.commit()
    session.refresh(db_prueba)
    return db_prueba


def listar_pre_sorteos(session: Session, sorteo_id: int) -> List[models.PreSorteo]:
    statement = (
        select(models.PreSorteo)
        .where(models.PreSorteo.sorteo_id == sorteo_id)
        .order_by(models.PreSorteo.numero_prueba)
    )
    return session.exec(statement).all()


def obtener_pre_sorteo(session: Session, sorteo_id: int, numero_prueba: int) -> Optional[models.PreSorteo]:
    statement = select(models.PreSorteo).where(
        models.PreSorteo.sorteo_id == sorteo_id,
        models.PreSorteo.numero_prueba == numero_prueba,
    )
    return session.exec(statement).first()


def guardar_resultado(session: Session, db_prueba: models.PreSorteo, numeros_ganadores: str) -> models.PreSorteo:
    cifras_esperadas = 7 if db_prueba.cantidad_balotas == 6 else 4

    if not numeros_ganadores.isdigit():
        raise ValueError("El resultado debe contener solo dígitos.")

    if len(numeros_ganadores) != cifras_esperadas:
        raise ValueError(f"Se esperan {cifras_esperadas} cifras para esta prueba.")

    db_prueba.numeros_ganadores = numeros_ganadores
    session.add(db_prueba)
    session.commit()
    session.refresh(db_prueba)
    return db_prueba


def eliminar_pre_sorteo(session: Session, db_prueba: models.PreSorteo) -> None:
    session.delete(db_prueba)
    session.commit()