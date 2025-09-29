from fastapi.testclient import TestClient
from app.security import create_email_token

def auth(client: TestClient, email: str):
    client.post("/auth/register", json={"email":email,"password":"password123"})
    token = create_email_token(email)
    client.get("/auth/verify-email", params={"token": token})
    r = client.post("/auth/login", data={"username":email,"password":"password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_contacts_crud_endpoints(client: TestClient):
    h = auth(client, "flow1@example.com")
    body = {"first_name":"Ann","last_name":"Lee","email":"ann@ex.com","phone":"55555","birthday":"1995-01-02","extra":"x"}
    r = client.post("/contacts", json=body, headers=h)
    assert r.status_code == 201
    cid = r.json()["id"]
    r2 = client.get("/contacts", headers=h)
    assert r2.status_code == 200 and len(r2.json()) >= 1
    r3 = client.get(f"/contacts/{cid}", headers=h)
    assert r3.status_code == 200 and r3.json()["id"] == cid
    r4 = client.put(f"/contacts/{cid}", json={"phone":"11111"}, headers=h)
    assert r4.status_code == 200 and r4.json()["phone"] == "11111"
    r5 = client.get("/contacts/birthdays/upcoming?days=365", headers=h)
    assert r5.status_code == 200
    r6 = client.delete(f"/contacts/{cid}", headers=h)
    assert r6.status_code in (204,200)
    r7 = client.get(f"/contacts/{cid}", headers=h)
    assert r7.status_code == 404
