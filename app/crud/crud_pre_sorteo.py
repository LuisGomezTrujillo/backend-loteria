from typing import List, Optional
from sqlmodel import Session, select

from app import models

MAX_PRUEBAS_POR_SORTEO = 10


def obtener_siguiente_numero_prueba(session: Session, sorteo_id: int) -> Optional[int]:
    """
    Devuelve el menor numero_prueba disponible (1..10) que NO esté ya usado
    por este sorteo. Esto hace que, si se borra la Prueba 3, la próxima
    prueba que se cree vuelva a ocupar el puesto 3 en vez de saltar al 6,
    manteniendo la secuencia 1..10 sin huecos permanentes.

    Devuelve None si las 10 posiciones ya están ocupadas.
    """
    statement = select(models.PreSorteo.numero_prueba).where(models.PreSorteo.sorteo_id == sorteo_id)
    numeros_usados = set(session.exec(statement).all())

    for candidato in range(1, MAX_PRUEBAS_POR_SORTEO + 1):
        if candidato not in numeros_usados:
            return candidato
    return None


def crear_pre_sorteo(session: Session, sorteo_id: int, cantidad_balotas: int = 6) -> models.PreSorteo:
    numero_prueba = obtener_siguiente_numero_prueba(session, sorteo_id)
    if numero_prueba is None:
        raise ValueError(
            f"Ya se registraron las {MAX_PRUEBAS_POR_SORTEO} pruebas posibles para este sorteo."
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