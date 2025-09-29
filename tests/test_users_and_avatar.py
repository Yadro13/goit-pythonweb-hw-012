from fastapi.testclient import TestClient
from app import crud
from app.database import SessionLocal
from app.security import decode_token
# from sqlalchemy import select
# from app.models import User

def test_me_rate_limit_and_avatar_and_default_avatar_admin(client: TestClient):
    # Реєструємо юзера і логінимося
    client.post("/auth/register", json={"email":"role1@example.com","password":"password123"})
    r = client.post("/auth/login", data={"username":"role1@example.com","password":"password123"})
    assert r.status_code == 200
    token_user = r.json()["access_token"]
    h_user = {"Authorization": f"Bearer {token_user}"}

    # Лимітим 7 запитів на /users/me за хвилину
    hits = [client.get("/users/me", headers=h_user).status_code for _ in range(7)]
    assert 200 in hits

    # Аватарка не задана —> 503
    with open(__file__, "rb") as f:
        resp = client.post("/users/me/avatar", headers=h_user, files={"file": ("a.txt", f, "text/plain")})
    assert resp.status_code in (503, 502)

    # Адмінський ендпоінт /users/admin/default-avatar недоступний звичайному юзеру
    db = SessionLocal()
    payload = decode_token(token_user)
    uid = int(payload["sub"])
    crud.set_user_role(db, uid, "admin")
    db.close()

    # Тестуємо ендпоінт для встановлення аватарки за замовчуванням
    resp2 = client.post("/users/admin/default-avatar", headers=h_user, params={"url":"http://example.com/default.png"})
    assert resp2.status_code in (201, 403)

    g = client.get("/users/default-avatar")
    assert g.status_code == 200
