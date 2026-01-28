import os
from sqlmodel import SQLModel, create_engine, Session

# 1. Obtenemos la URL de la base de datos de las variables de entorno
# Si no existe (estamos en local), usamos SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Fix necesario para SQLAlchemy con Render (postgres:// -> postgresql://)
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Si no hay variable de entorno, usamos un archivo local
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./database.db"

# 2. Creamos el motor de conexión
# connect_args es necesario solo para SQLite
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 3. Función para crear las tablas
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 4. Dependencia para obtener la sesión en cada petición
def get_session():
    with Session(engine) as session:
        yield session