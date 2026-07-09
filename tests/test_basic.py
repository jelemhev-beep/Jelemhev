import subprocess

from fastapi.testclient import TestClient

from app import search as search_index
from app.config import REPOS_DIR
from app.db import get_connection
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


def test_search_finds_pushed_code_by_subword(tmp_path):
    client = TestClient(app)
    client.post("/register", data={"username": "dave", "password": "hunter22"})
    resp = client.post("/repos/new", data={"name": "searchable", "description": ""}, follow_redirects=False)
    assert resp.status_code == 303

    repo_path = REPOS_DIR / "dave" / "searchable.git"
    work = tmp_path / "work"
    subprocess.run(["git", "clone", str(repo_path), str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "dave@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "Dave"], check=True)
    (work / "auth.py").write_text("def authenticate_user(username):\n    return True\n")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "add auth"], check=True)
    subprocess.run(["git", "-C", str(work), "push", "origin", "HEAD:main"], check=True, capture_output=True)

    conn = get_connection()
    user_id = conn.execute("SELECT id FROM users WHERE username = ?", ("dave",)).fetchone()["id"]
    conn.close()

    assert search_index.index_repository(user_id, "dave", "searchable") == 1

    # subword match: "authenticate" alone must find "authenticate_user"
    results = search_index.search(user_id, "dave", "authenticate")
    assert len(results) == 1
    assert results[0]["repo_name"] == "searchable"
    assert results[0]["filepath"] == "auth.py"

    assert search_index.search(user_id, "dave", "nonexistentterm") == []
