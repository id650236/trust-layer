from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_principal():
    r = client.post("/v1/principals", json={
        "principal_name": "demo-loan-bot",
        "owner_id": "owner:demo-bank",
        "principal_type": "agent",
        "profile": "banking",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["principal_name"] == "demo-loan-bot"
    assert data["principal_type"] == "agent"
    assert data["public_key_jwk"]["kty"] == "OKP"
    assert data["public_key_jwk"]["crv"] == "Ed25519"
    assert "private_key_b64" in data
    assert len(data["private_key_b64"]) > 20
    assert data["status"] == "active"

def test_get_principal():
    # Create one
    r = client.post("/v1/principals", json={
        "principal_name": "get-test-bot",
        "owner_id": "owner:test",
        "principal_type": "agent",
        "profile": "default",
    })
    assert r.status_code == 201, r.text
    pid = r.json()["principal_id"]

    # Read it back
    r2 = client.get(f"/v1/principals/{pid}")
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["principal_id"] == pid
    assert data["principal_name"] == "get-test-bot"
    # Critical: the private key must NEVER be returned here
    assert "private_key_b64" not in data


def test_get_principal_not_found():
    r = client.get("/v1/principals/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404