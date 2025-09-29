import fakeredis
from app import cache
from app.settings import settings

def test_cache_disabled_without_url(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", "")
    assert cache.get_redis() is None
    cache.cache_user(None)
    assert cache.get_cached_user(1) is None

def test_cache_with_fakeredis(monkeypatch):
    # Provide module-level from_url() for our monkeypatch
    r = fakeredis.FakeRedis(decode_responses=True)
    class DummyRedisModule:
        @staticmethod
        def from_url(url, decode_responses=True):
            return r
    monkeypatch.setattr(cache, "redis", DummyRedisModule)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://dummy/0")
    class U:
        def __init__(self):
            self.id=123; self.email="x@e.com"; self.is_active=True; self.is_verified=True; self.avatar_url=None; self.role="user"
    u = U()
    cache.cache_user(u, ttl=1)
    data = cache.get_cached_user(123)
    assert data and data["email"] == "x@e.com"
    cache.invalidate_user(123)
    assert cache.get_cached_user(123) is None
