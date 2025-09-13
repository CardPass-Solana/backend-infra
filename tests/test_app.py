from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_read_item_without_q():
    r = client.get("/items/42")
    assert r.status_code == 200
    assert r.json() == {"item_id": 42, "q": None}


def test_read_item_with_q():
    r = client.get("/items/42?q=hello")
    assert r.status_code == 200
    assert r.json() == {"item_id": 42, "q": "hello"}
