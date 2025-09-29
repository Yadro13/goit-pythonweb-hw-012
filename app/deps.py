import time
from typing import Dict, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .settings import settings
from .security import decode_token
from .cache import get_cached_user, cache_user
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Проста in-memory rate-limit для /me (не для продакшну з кількома процесами)
_calls: Dict[int, List[float]] = {}

def rate_limit_me(user_id: int):
    now = time.time()
    window = settings.RATE_LIMIT_ME_WINDOW_SEC
    max_calls = settings.RATE_LIMIT_ME_CALLS
    lst = _calls.setdefault(user_id, [])
    lst[:] = [t for t in lst if now - t < window]
    if len(lst) >= max_calls:
        raise HTTPException(status_code=429, detail="Too Many Requests on /me")
    lst.append(now)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Повертає поточного користувача за JWT, використовуючи кеш Redis."""
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    cached = get_cached_user(int(sub))
    if cached:
        # Створюємо об'єкт User-подібний (легка реконструкція)
        user = db.get(models.User, int(sub))
        if user:
            return user
    user = db.get(models.User, int(sub))
    if user:
        cache_user(user)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")
    return user

def require_verified(user: models.User = Depends(get_current_user)) -> models.User:
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email is not verified")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Перевіряє, що користувач має роль admin."""
    if getattr(user, 'role', 'user') != 'admin':
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
