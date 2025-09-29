from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt
from passlib.context import CryptContext
from .settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Хешуємо пароль (український коментар)
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str | int, expires_minutes: int | None = None, scope: str = "access") -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire, "scope": scope}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_email_token(email: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)
    data = {"sub": email, "scope": "email_verification", "exp": expire}
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


import uuid

def create_refresh_token(subject: str | int) -> str:
    """Створює refresh-токен з довшим строком життя та унікальним JTI."""
    expire = datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "scope": "refresh", "jti": jti}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_password_reset_token(email: str) -> str:
    """Токен для скидання пароля; scope=password_reset."""
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    payload: dict[str, Any] = {"sub": email, "exp": expire, "scope": "password_reset"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
