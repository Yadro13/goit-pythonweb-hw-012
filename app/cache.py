"""Кешування через Redis.

Функції у цьому модулі інкапсулюють взаємодію з Redis, щоб повторно
використовувати підключення та спростити тестування (можна підмінити клієнт). 
"""
from __future__ import annotations
import json
from typing import Optional, Any, Dict
from .settings import settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # дозволяє тестам працювати без реального Redis

_client = None

def get_redis():
    """Повертає singleton-клієнт Redis або None, якщо REDIS_URL не задано."""
    global _client
    if settings.REDIS_URL is None or not settings.REDIS_URL:
        return None
    if redis is None:
        return None
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client

def cache_user(user: Any, ttl: int | None = None) -> None:
    """Кешуємо користувача за ключем user:{id}."""
    r = get_redis()
    if not r or not user:
        return
    data = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url,
        "role": getattr(user, "role", "user"),
    }
    r.setex(f"user:{user.id}", ttl or settings.CACHE_USER_TTL_SEC, json.dumps(data))

def get_cached_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Читає з кешу користувача за ідентифікатором."""
    r = get_redis()
    if not r:
        return None
    s = r.get(f"user:{user_id}")
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None

def invalidate_user(user_id: int) -> None:
    """Видаляє кеш користувача (коли змінюємо профіль/аватар)."""
    r = get_redis()
    if not r:
        return
    r.delete(f"user:{user_id}")
