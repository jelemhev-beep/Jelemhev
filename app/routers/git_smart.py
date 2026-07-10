import base64

from fastapi import APIRouter, HTTPException, Request

from .. import search as search_index
from ..config import REPOS_DIR
from ..db import get_connection
from ..git_http import git_http_backend
from ..security import DUMMY_PASSWORD_HASH, verify_password

router = APIRouter()


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": 'Basic realm="git"'},
    )


def _authenticate(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Basic "):
        raise _unauthorized()
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        username, _, password = decoded.partition(":")
    except Exception:
        raise _unauthorized()

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()

    password_hash = row["password_hash"] if row else DUMMY_PASSWORD_HASH
    password_ok = verify_password(password, password_hash)
    if not row or not password_ok:
        raise _unauthorized()
    return row


@router.api_route("/{owner}/{repo_name}.git/{path:path}", methods=["GET", "POST"])
async def git_backend_route(owner: str, repo_name: str, path: str, request: Request):
    user_row = _authenticate(request)
    username = user_row["username"]
    if username != owner:
        # Private, personal-use repos: only the owner may read or write.
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_connection()
    try:
        repo = conn.execute(
            """
            SELECT r.id FROM repositories r
            JOIN users u ON u.id = r.owner_id
            WHERE u.username = ? AND r.name = ?
            """,
            (owner, repo_name),
        ).fetchone()
    finally:
        conn.close()

    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    path_info = f"/{owner}/{repo_name}.git/{path}"
    response = await git_http_backend(request, path_info, REPOS_DIR, remote_user=username)

    if request.method == "POST" and path.endswith("git-receive-pack") and response.status_code == 200:
        try:
            search_index.index_repository(user_row["id"], username, repo_name)
        except Exception:
            pass  # indexing must never break a push

    return response
