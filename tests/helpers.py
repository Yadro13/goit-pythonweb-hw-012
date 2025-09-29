from fastapi.testclient import TestClient
from app import security

def register_and_login(client: TestClient, email: str, password: str) -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return r.json()["access_token"]

def verify_email_for(client: TestClient, email: str) -> None:
    token = security.create_email_token(email)
    client.get("/auth/verify-email", params={"token": token})
