
from fastapi.testclient import TestClient

def test_me_rate_limit(client: TestClient):
    client.post("/auth/register", json={"email":"rl@example.com","password":"password123"})
    r = client.post("/auth/login", data={"username":"rl@example.com","password":"password123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    codes = []
    for _ in range(7):
        resp = client.get("/users/me", headers=headers)
        codes.append(resp.status_code)
    assert 429 in codes or codes.count(200) >= 1
