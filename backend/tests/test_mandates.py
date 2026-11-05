from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _create_principal():
    r = client.post("/v1/principals", json={
        "principal_name": "mandate-test-bot",
        "owner_id": "owner:test",
        "principal_type": "agent",
        "profile": "banking",
    })
    assert r.status_code == 201, r.text
    return r.json()["principal_id"]


def test_create_mandate():
    pid = _create_principal()
    r = client.post(f"/v1/principals/{pid}/mandates", json={
        "allowed_actions": ["payment.initiate", "invoice.approve"],
        "constraints": {"max_amount_eur": 100, "per_day": 10},
        "valid_for_hours": 48,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["principal_id"] == pid
    assert "payment.initiate" in data["allowed_actions"]
    assert data["constraints"]["max_amount_eur"] == 100
    assert data["status"] == "active"


def test_create_mandate_principal_not_found():
    r = client.post(
        "/v1/principals/00000000-0000-0000-0000-000000000000/mandates",
        json={"allowed_actions": ["x"], "constraints": {}},
    )
    assert r.status_code == 404


def test_list_mandates():
    pid = _create_principal()
    client.post(f"/v1/principals/{pid}/mandates", json={
        "allowed_actions": ["a"], "constraints": {}, "valid_for_hours": 1,
    })
    client.post(f"/v1/principals/{pid}/mandates", json={
        "allowed_actions": ["b"], "constraints": {}, "valid_for_hours": 1,
    })
    r = client.get(f"/v1/principals/{pid}/mandates")
    assert r.status_code == 200, r.text
    assert len(r.json()) == 2