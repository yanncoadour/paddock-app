import os
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.engine import Engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret")


def get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALG", "HS256")


def create_access_token(subject: str, expires_minutes: int = 60 * 24 * 7) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()])


def is_beta_allowed(engine: Engine, email: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM beta_whitelist_emails WHERE email = :email"),
            {"email": email},
        )
        return result.first() is not None
