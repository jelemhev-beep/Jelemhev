from fastapi.testclient import TestClient

from app.main import app


def test_register_and_dashboard():
    client = TestClient(app)

    resp = client.get("/register")
    assert resp.status_code == 200

    resp = client.post("/register", data={"username": "alice", "password": "hunter22"}, follow_redirects=False)
    assert resp.status_code == 303

    resp = client.get("/register")
    assert "ferm" in resp.text.lower()

    resp = client.get("/")
    assert resp.status_code == 200
    assert "alice" in resp.text


def test_create_repo_and_browse():
    client = TestClient(app)
    client.post("/register", data={"username": "bob", "password": "hunter22"})

    resp = client.post(
        "/repos/new", data={"name": "myrepo", "description": "test repo"}, follow_redirects=False
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/bob/myrepo"

    resp = client.get("/bob/myrepo")
    assert resp.status_code == 200
    assert "Depot vide" in resp.text or "vide" in resp.text.lower()


def test_login_wrong_password():
    client = TestClient(app)
    client.post("/register", data={"username": "carol", "password": "hunter22"})
    client.get("/logout")
    resp = client.post("/login", data={"username": "carol", "password": "wrong"})
    assert resp.status_code == 401
