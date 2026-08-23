"""
Seguridad: hashing de contraseñas (bcrypt) y JWT para la cookie de sesión.

Variables de entorno requeridas en Render (¡no las dejes con el valor
por defecto en producción!):

    JWT_SECRET_KEY=<una cadena larga y aleatoria>
    JWT_EXPIRE_MINUTES=480   (opcional, default 8 horas)
"""
import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CAMBIA-ESTA-CLAVE-EN-PRODUCCION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas (un turno)

COOKIE_NAME = "mzl_access_token"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    # Lanza jwt.ExpiredSignatureError / jwt.InvalidTokenError si algo falla
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])