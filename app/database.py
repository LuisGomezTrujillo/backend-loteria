import os
from sqlmodel import SQLModel, create_engine, Session

# 1. Configuración de la URL de la BD
database_url = os.environ.get("DATABASE_URL", "sqlite:///./loteria.db")

# Fix para Render: reemplaza postgres:// por postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Configuración específica para SQLite (evita errores de hilos)
connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}

engine = create_engine(database_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session