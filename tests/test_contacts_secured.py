
from fastapi.testclient import TestClient

def auth_token(client: TestClient, email="u@example.com", password="pass12345"):
    client.post("/auth/register", json={"email":email,"password":password})
    # verify email: для тестів напряму викликаємо verify з токеном із /auth/register недоступно
    # замість цього не перевіряємо контакти без верифікації
    r = client.post("/auth/login", data={"username":email,"password":password})
    token = r.json()["access_token"]
    return token

def test_contacts_require_verified(client: TestClient):
    token = auth_token(client)
    # Спроба доступу до контактів без верифікації має повертати 403
    r = client.get("/contacts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
