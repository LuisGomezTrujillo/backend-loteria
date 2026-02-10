import os
from sqlmodel import SQLModel, create_engine, Session

# 1. Obtenemos la URL de la variable de entorno
# Si no existe (desarrollo local), usará SQLite por defecto
database_url = os.environ.get("DATABASE_URL", "sqlite:///./loteria.db")

# 2. FIX CRÍTICO PARA RENDER: 
# Render entrega URLs que empiezan con 'postgres://', 
# pero SQLAlchemy requiere 'postgresql://'
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# 3. Configuración del motor (engine)
# El check_same_thread es solo para SQLite
connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}

engine = create_engine(database_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
