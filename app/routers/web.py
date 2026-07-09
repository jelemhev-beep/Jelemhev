from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import git_utils
from ..config import REPOS_DIR, TEMPLATES_DIR
from ..db import get_connection
from ..git_utils import GitError
from ..security import hash_password, verify_password

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def current_user(request: Request):
    username = request.session.get("username")
    if not username:
        return None
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()


def _require_owner(request: Request, owner: str):
    user = current_user(request)
    if user is None or user["username"] != owner:
        raise HTTPException(status_code=404, detail="Depot introuvable")
    return user


def _get_repo_or_404(owner: str, name: str):
    conn = get_connection()
    try:
        repo = conn.execute(
            """
            SELECT r.*, u.username as owner FROM repositories r
            JOIN users u ON u.id = r.owner_id
            WHERE u.username = ? AND r.name = ?
            """,
            (owner, name),
        ).fetchone()
    finally:
        conn.close()
    if repo is None:
        raise HTTPException(status_code=404, detail="Depot introuvable")
    return repo


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = current_user(request)
    if user is None:
        return RedirectResponse("/login")
    conn = get_connection()
    try:
        repos = conn.execute(
            "SELECT * FROM repositories WHERE owner_id = ? ORDER BY created_at DESC", (user["id"],)
        ).fetchall()
    finally:
        conn.close()
    return templates.TemplateResponse(request, "dashboard.html", {"user": user, "repos": repos})


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    if current_user(request):
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()
    if not row or not verify_password(password, row["password_hash"]):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Identifiants invalides"}, status_code=401
        )
    request.session["username"] = row["username"]
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    finally:
        conn.close()
    if count > 0:
        return templates.TemplateResponse(request, "register_closed.html", {})
    return templates.TemplateResponse(request, "register.html", {"error": None})


@router.post("/register")
async def register_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if count > 0:
            return templates.TemplateResponse(request, "register_closed.html", {}, status_code=403)
        if len(username) < 3 or len(password) < 8 or not username.replace("_", "").isalnum():
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Nom d'utilisateur (3+ car. alphanumeriques) et mot de passe (8+ car.) requis"},
                status_code=400,
            )
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
    finally:
        conn.close()
    request.session["username"] = username
    return RedirectResponse("/", status_code=303)


@router.post("/repos/new")
async def create_repo(request: Request, name: str = Form(...), description: str = Form("")):
    user = current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    name = name.strip()
    if not name or not all(c.isalnum() or c in "-_." for c in name):
        raise HTTPException(status_code=400, detail="Nom de depot invalide")

    repo_path = REPOS_DIR / user["username"] / f"{name}.git"
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM repositories WHERE owner_id = ? AND name = ?", (user["id"], name)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Un depot avec ce nom existe deja")
        git_utils.init_bare_repo(repo_path)
        conn.execute(
            "INSERT INTO repositories (owner_id, name, description) VALUES (?, ?, ?)",
            (user["id"], name, description),
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(f"/{user['username']}/{name}", status_code=303)


@router.get("/{owner}/{name}", response_class=HTMLResponse)
async def repo_home(request: Request, owner: str, name: str):
    user = _require_owner(request, owner)
    repo = _get_repo_or_404(owner, name)
    repo_path = REPOS_DIR / owner / f"{name}.git"
    branch = git_utils.default_branch(repo_path)
    entries = []
    commits = []
    error = None
    if branch:
        try:
            entries = git_utils.list_tree(repo_path, branch)
            commits = git_utils.log(repo_path, branch, limit=5)
        except GitError as exc:
            error = str(exc)
    clone_url = f"{request.base_url}{owner}/{name}.git"
    return templates.TemplateResponse(
        request,
        "repo_home.html",
        {
            "user": user,
            "repo": repo,
            "branch": branch,
            "entries": entries,
            "commits": commits,
            "error": error,
            "clone_url": clone_url,
        },
    )


@router.get("/{owner}/{name}/tree/{ref}/{subpath:path}", response_class=HTMLResponse)
async def repo_tree(request: Request, owner: str, name: str, ref: str, subpath: str = ""):
    user = _require_owner(request, owner)
    repo = _get_repo_or_404(owner, name)
    repo_path = REPOS_DIR / owner / f"{name}.git"
    try:
        entries = git_utils.list_tree(repo_path, ref, subpath)
    except GitError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return templates.TemplateResponse(
        request,
        "repo_tree.html",
        {
            "user": user,
            "repo": repo,
            "branch": ref,
            "entries": entries,
            "subpath": subpath,
        },
    )


@router.get("/{owner}/{name}/blob/{ref}/{filepath:path}", response_class=HTMLResponse)
async def repo_blob(request: Request, owner: str, name: str, ref: str, filepath: str):
    user = _require_owner(request, owner)
    repo = _get_repo_or_404(owner, name)
    repo_path = REPOS_DIR / owner / f"{name}.git"
    try:
        content = git_utils.read_file(repo_path, ref, filepath)
    except GitError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return templates.TemplateResponse(
        request,
        "repo_blob.html",
        {
            "user": user,
            "repo": repo,
            "branch": ref,
            "filepath": filepath,
            "content": content,
        },
    )


@router.get("/{owner}/{name}/commits/{ref}", response_class=HTMLResponse)
async def repo_commits(request: Request, owner: str, name: str, ref: str):
    user = _require_owner(request, owner)
    repo = _get_repo_or_404(owner, name)
    repo_path = REPOS_DIR / owner / f"{name}.git"
    try:
        commits = git_utils.log(repo_path, ref, limit=50)
    except GitError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return templates.TemplateResponse(
        request,
        "repo_commits.html",
        {"user": user, "repo": repo, "branch": ref, "commits": commits},
    )


@router.get("/{owner}/{name}/commit/{sha}", response_class=HTMLResponse)
async def repo_commit(request: Request, owner: str, name: str, sha: str):
    user = _require_owner(request, owner)
    repo = _get_repo_or_404(owner, name)
    repo_path = REPOS_DIR / owner / f"{name}.git"
    try:
        diff = git_utils.show_commit(repo_path, sha)
    except GitError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return templates.TemplateResponse(
        request,
        "repo_commit.html",
        {"user": user, "repo": repo, "sha": sha, "diff": diff},
    )
