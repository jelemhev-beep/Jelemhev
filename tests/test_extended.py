import subprocess

from fastapi.testclient import TestClient

from app import search as search_index
from app.config import REPOS_DIR
from app.db import get_connection
from app.main import app
from app.security import hash_password


def _register(client, username, password="hunter22"):
    return client.post("/register", data={"username": username, "password": password})


def _insert_user_directly(username, password="hunter22"):
    """Simulate `scripts/create_user.py`: add a second account without going
    through the (single-admin) /register endpoint."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
    finally:
        conn.close()
    return user_id


def _push_file(client, owner, repo_name, tmp_path, filename, content, workdir_name="work"):
    repo_path = REPOS_DIR / owner / f"{repo_name}.git"
    work = tmp_path / workdir_name
    subprocess.run(["git", "clone", str(repo_path), str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", f"{owner}@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", owner], check=True)
    target = work / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "add file"], check=True)
    subprocess.run(["git", "-C", str(work), "push", "origin", "HEAD:main"], check=True, capture_output=True)


def _user_id(username):
    conn = get_connection()
    try:
        return conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 1. Isolation stricte entre utilisateurs
# ---------------------------------------------------------------------------


def test_user_b_cannot_browse_or_search_user_a_repo(tmp_path):
    client_a = TestClient(app)
    _register(client_a, "alice")
    resp = client_a.post("/repos/new", data={"name": "secret", "description": "private"}, follow_redirects=False)
    assert resp.status_code == 303

    _push_file(client_a, "alice", "secret", tmp_path, "topsecret.py", "def zzzqrxtoken():\n    return 1\n")

    alice_id = _user_id("alice")
    assert search_index.index_repository(alice_id, "alice", "secret") == 1

    # bob is created directly (registration is closed after the first user)
    _insert_user_directly("bob", "hunter22")
    client_b = TestClient(app)
    resp = client_b.post("/login", data={"username": "bob", "password": "hunter22"}, follow_redirects=False)
    assert resp.status_code == 303

    # bob must never be able to see alice's repository
    assert client_b.get("/alice/secret").status_code == 404
    assert client_b.get("/alice/secret/tree/main/").status_code == 404
    assert client_b.get("/alice/secret/blob/main/topsecret.py").status_code == 404
    assert client_b.get("/alice/secret/commits/main").status_code == 404
    assert client_b.get("/alice/secret/commit/deadbeef").status_code == 404

    # bob's dashboard must not list alice's repo either
    dash = client_b.get("/")
    assert "secret" not in dash.text

    # bob's search must not surface alice's content, even though alice's own search does
    resp_b = client_b.get("/search?q=zzzqrxtoken")
    assert resp_b.status_code == 200
    assert "topsecret" not in resp_b.text

    resp_a = client_a.get("/search?q=zzzqrxtoken")
    assert resp_a.status_code == 200
    assert "topsecret" in resp_a.text


def test_direct_search_index_is_scoped_per_owner(tmp_path):
    client_a = TestClient(app)
    _register(client_a, "erin")
    client_a.post("/repos/new", data={"name": "priv", "description": ""}, follow_redirects=False)
    _push_file(client_a, "erin", "priv", tmp_path, "keys.py", "def uniquemarkerabc():\n    pass\n")

    erin_id = _user_id("erin")
    assert search_index.index_repository(erin_id, "erin", "priv") == 1

    bob_id = _insert_user_directly("frank", "hunter22")

    # frank has no repos indexed at all: search under his own owner_id is empty
    assert search_index.search(bob_id, "frank", "uniquemarkerabc") == []
    # erin can find it under her own owner_id
    assert len(search_index.search(erin_id, "erin", "uniquemarkerabc")) == 1


# ---------------------------------------------------------------------------
# 2. Validation du nom de depot
# ---------------------------------------------------------------------------


def test_repo_name_rejects_invalid_characters():
    client = TestClient(app)
    _register(client, "gina")

    resp = client.post("/repos/new", data={"name": "bad name!", "description": ""})
    assert resp.status_code == 400


def test_repo_name_rejects_path_with_slash():
    client = TestClient(app)
    _register(client, "hank")

    resp = client.post("/repos/new", data={"name": "../escape", "description": ""})
    assert resp.status_code == 400

    resp = client.post("/repos/new", data={"name": "sub/dir", "description": ""})
    assert resp.status_code == 400

    # nothing should have been created on disk outside REPOS_DIR/hank
    assert not (REPOS_DIR / "escape.git").exists()
    assert not (REPOS_DIR / "sub").exists()


def test_repo_name_duplicate_for_same_owner_is_rejected():
    client = TestClient(app)
    _register(client, "iris")

    resp = client.post("/repos/new", data={"name": "dup", "description": ""}, follow_redirects=False)
    assert resp.status_code == 303

    resp = client.post("/repos/new", data={"name": "dup", "description": "again"})
    assert resp.status_code == 400

    conn = get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM repositories WHERE name = 'dup'"
        ).fetchone()["c"]
    finally:
        conn.close()
    assert count == 1


# ---------------------------------------------------------------------------
# 3. /login, /logout, /register apres qu'un compte existe deja
# ---------------------------------------------------------------------------


def test_second_register_is_refused():
    client = TestClient(app)
    resp = client.post(
        "/register", data={"username": "julia", "password": "hunter22"}, follow_redirects=False
    )
    assert resp.status_code == 303

    # the register form now shows "closed" for anyone, including logged-out visitors
    fresh = TestClient(app)
    resp = fresh.get("/register")
    assert resp.status_code == 200
    assert "ferm" in resp.text.lower()

    resp = fresh.post("/register", data={"username": "mallory", "password": "whatever1"})
    assert resp.status_code == 403

    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        mallory = conn.execute("SELECT id FROM users WHERE username = ?", ("mallory",)).fetchone()
    finally:
        conn.close()
    assert count == 1
    assert mallory is None


def test_logout_then_login_cycle():
    client = TestClient(app)
    _register(client, "kevin")

    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"

    # after logout, dashboard is no longer accessible
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)
    assert resp.headers["location"] == "/login"

    # wrong password still rejected (existing behaviour, sanity check)
    resp = client.post("/login", data={"username": "kevin", "password": "wrongpass"})
    assert resp.status_code == 401

    # correct password logs back in
    resp = client.post("/login", data={"username": "kevin", "password": "hunter22"}, follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"

    resp = client.get("/")
    assert resp.status_code == 200
    assert "kevin" in resp.text


# ---------------------------------------------------------------------------
# 4. Recherche : terme absent / match par nom de fichier
# ---------------------------------------------------------------------------


def test_search_absent_term_returns_empty(tmp_path):
    client = TestClient(app)
    _register(client, "liam")
    client.post("/repos/new", data={"name": "codebase", "description": ""}, follow_redirects=False)
    _push_file(client, "liam", "codebase", tmp_path, "main.py", "print('hello')\n")

    liam_id = _user_id("liam")
    search_index.index_repository(liam_id, "liam", "codebase")

    assert search_index.search(liam_id, "liam", "totallyabsentterm") == []

    resp = client.get("/search?q=totallyabsentterm")
    assert resp.status_code == 200
    assert "Aucun resultat" in resp.text


def test_search_matches_term_present_only_in_filename(tmp_path):
    client = TestClient(app)
    _register(client, "mona")
    client.post("/repos/new", data={"name": "app", "description": ""}, follow_redirects=False)
    # the token "credentials" appears in the file NAME only, never in its content
    _push_file(client, "mona", "app", tmp_path, "credentials_loader.py", "x = 1\ny = 2\n")

    mona_id = _user_id("mona")
    assert search_index.index_repository(mona_id, "mona", "app") == 1

    results = search_index.search(mona_id, "mona", "credentials")
    assert len(results) == 1
    assert results[0]["filepath"] == "credentials_loader.py"

    resp = client.get("/search?q=credentials")
    assert resp.status_code == 200
    assert "credentials_loader.py" in resp.text


# ---------------------------------------------------------------------------
# 5. Owner/repo inexistant -> 404 propre
# ---------------------------------------------------------------------------


def test_unknown_repo_and_owner_return_clean_404(tmp_path):
    client = TestClient(app)
    _register(client, "nina")
    client.post("/repos/new", data={"name": "myrepo", "description": ""}, follow_redirects=False)
    _push_file(client, "nina", "myrepo", tmp_path, "a.txt", "hello\n")

    # unknown repo name for a real (and currently logged-in) owner
    resp = client.get("/nina/doesnotexist")
    assert resp.status_code == 404

    # unknown owner entirely
    resp = client.get("/ghostowner/doesnotexist")
    assert resp.status_code == 404

    # unknown subpath / file / commit within a real repo
    assert client.get("/nina/myrepo/tree/main/no/such/dir").status_code == 404
    assert client.get("/nina/myrepo/blob/main/nosuchfile.txt").status_code == 404
    assert client.get("/nina/myrepo/commit/deadbeefdeadbeef").status_code == 404

    # logged-out access to an existing repo must also 404 cleanly, not crash
    anon = TestClient(app)
    resp = anon.get("/nina/myrepo")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6. Routes protegees redirigent vers /login si non connecte
# ---------------------------------------------------------------------------


def test_protected_routes_redirect_to_login_when_anonymous():
    client = TestClient(app)

    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)
    assert resp.headers["location"] == "/login"

    resp = client.post("/repos/new", data={"name": "whatever", "description": ""}, follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"

    resp = client.post("/reindex", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"

    resp = client.get("/search?q=foo", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
