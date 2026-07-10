import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(Exception):
    pass


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def init_bare_repo(path: Path) -> None:
    if path.exists():
        raise GitError("Repository already exists")
    path.mkdir(parents=True)
    result = subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip())


def default_branch(path: Path) -> str | None:
    try:
        out = _run(["symbolic-ref", "--short", "HEAD"], cwd=path)
    except GitError:
        return None
    branch = out.strip()
    heads = _run(["for-each-ref", "--format=%(refname:short)", "refs/heads/"], cwd=path)
    if branch not in heads.splitlines():
        return None
    return branch


def list_branches(path: Path) -> list[str]:
    out = _run(["for-each-ref", "--format=%(refname:short)", "refs/heads/"], cwd=path)
    return [line for line in out.splitlines() if line]


@dataclass
class TreeEntry:
    mode: str
    type: str
    sha: str
    size: str
    name: str


def list_tree(path: Path, ref: str, subpath: str = "") -> list[TreeEntry]:
    target = f"{ref}:{subpath}" if subpath else f"{ref}:"
    out = _run(["ls-tree", "-l", "--end-of-options", target], cwd=path)
    entries = []
    for line in out.splitlines():
        if not line:
            continue
        meta, name = line.split("\t", 1)
        mode, type_, sha, size = meta.split()
        entries.append(TreeEntry(mode, type_, sha, size, name))
    entries.sort(key=lambda e: (e.type != "tree", e.name.lower()))
    return entries


def read_file(path: Path, ref: str, filepath: str) -> str:
    return _run(["show", "--end-of-options", f"{ref}:{filepath}"], cwd=path)


def read_blob_bytes(path: Path, ref: str, filepath: str) -> bytes:
    result = subprocess.run(
        ["git", "show", "--end-of-options", f"{ref}:{filepath}"], cwd=path, capture_output=True
    )
    if result.returncode != 0:
        raise GitError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def list_tree_recursive(path: Path, ref: str) -> list[tuple[str, str]]:
    """All blobs (file, sha) reachable from ref, at any depth."""
    out = _run(["ls-tree", "-r", "--end-of-options", ref], cwd=path)
    files = []
    for line in out.splitlines():
        if not line:
            continue
        meta, name = line.split("\t", 1)
        _mode, type_, sha = meta.split()
        if type_ == "blob":
            files.append((name, sha))
    return files


@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    author: str
    date: str
    message: str


def log(path: Path, ref: str = "HEAD", limit: int = 30, skip: int = 0) -> list[CommitInfo]:
    fmt = "%H%x01%h%x01%an%x01%ad%x01%s"
    out = _run(
        [
            "log",
            f"--max-count={limit}",
            f"--skip={skip}",
            "--date=iso-local",
            f"--pretty=format:{fmt}",
            "--end-of-options",
            ref,
        ],
        cwd=path,
    )
    commits = []
    for line in out.splitlines():
        if not line:
            continue
        sha, short_sha, author, date, message = line.split("\x01")
        commits.append(CommitInfo(sha, short_sha, author, date, message))
    return commits


def show_commit(path: Path, sha: str) -> str:
    return _run(["show", "--patch", "--stat", "--end-of-options", sha], cwd=path)


def repo_size_kb(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total // 1024
