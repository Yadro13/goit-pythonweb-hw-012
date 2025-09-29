from fastapi.testclient import TestClient
from app.security import create_email_token

def test_register_login_refresh_and_verify(client: TestClient):
    r = client.post("/auth/register", json={"email":"e2@example.com","password":"pass12345"})
    assert r.status_code == 201
    r2 = client.post("/auth/login", data={"username":"e2@example.com","password":"bad"})
    assert r2.status_code == 401
    r3 = client.post("/auth/login", data={"username":"e2@example.com","password":"pass12345"})
    data = r3.json()
    assert "access_token" in data and "refresh_token" in data
    # bad refresh
    r4 = client.post("/auth/refresh", json={"refresh_token":"xxx"})
    assert r4.status_code in (400,401,422)
    # good refresh (expects JSON body)
    r5 = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r5.status_code == 200
    # email verify bad/good
    rv_bad = client.get("/auth/verify-email", params={"token":"abc"})
    assert rv_bad.status_code in (400,401)
    token = create_email_token("e2@example.com")
    rv_ok = client.get("/auth/verify-email", params={"token": token})
    assert rv_ok.status_code in (200, 422)
