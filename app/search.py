import math
import re

from . import git_utils
from .config import REPOS_DIR
from .db import get_connection

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
SUBWORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")
MAX_FILE_SIZE = 300_000  # bytes; larger files are skipped, not indexed
MAX_LINE_LEN = 2000
MAX_TOKEN_LEN = 40


def _subwords(raw: str) -> list[str]:
    """Split identifiers on snake_case/camelCase boundaries so that
    e.g. `authenticate_user` is also findable by just `authenticate`.
    """
    parts = []
    for chunk in raw.split("_"):
        if chunk:
            parts.extend(SUBWORD_RE.findall(chunk))
    return parts


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in TOKEN_RE.findall(text):
        if len(raw) > MAX_TOKEN_LEN:
            continue
        whole = raw.lower()
        if len(whole) > 1:
            tokens.append(whole)
        for sub in _subwords(raw):
            sub_low = sub.lower()
            if len(sub_low) > 1 and sub_low != whole:
                tokens.append(sub_low)
    return tokens


def _is_binary(data: bytes) -> bool:
    return b"\x00" in data[:8000]


def index_repository(owner_id: int, username: str, repo_name: str) -> int:
    """(Re)index one repository's default branch. Incremental: unchanged
    blobs (same sha) are skipped, deleted files are pruned. Returns the
    number of files (re)indexed.
    """
    repo_path = REPOS_DIR / username / f"{repo_name}.git"
    branch = git_utils.default_branch(repo_path)
    if not branch:
        return 0

    conn = get_connection()
    indexed = 0
    try:
        existing = {
            row["filepath"]: (row["id"], row["blob_sha"])
            for row in conn.execute(
                "SELECT id, filepath, blob_sha FROM search_documents WHERE owner_id = ? AND repo_name = ?",
                (owner_id, repo_name),
            )
        }
        seen_paths = set()

        for filepath, sha in git_utils.list_tree_recursive(repo_path, branch):
            seen_paths.add(filepath)
            if filepath in existing and existing[filepath][1] == sha:
                continue

            try:
                data = git_utils.read_blob_bytes(repo_path, branch, filepath)
            except git_utils.GitError:
                continue
            if len(data) > MAX_FILE_SIZE or _is_binary(data):
                continue
            text = data.decode("utf-8", errors="ignore")

            if filepath in existing:
                doc_id = existing[filepath][0]
                conn.execute("DELETE FROM search_postings WHERE document_id = ?", (doc_id,))
                conn.execute(
                    "UPDATE search_documents SET blob_sha = ?, line_count = ?, indexed_at = datetime('now') WHERE id = ?",
                    (sha, text.count("\n") + 1, doc_id),
                )
            else:
                cur = conn.execute(
                    "INSERT INTO search_documents (owner_id, repo_name, filepath, blob_sha, line_count) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (owner_id, repo_name, filepath, sha, text.count("\n") + 1),
                )
                doc_id = cur.lastrowid

            postings: set[tuple[str, int]] = set()
            for line_number, line in enumerate(text.splitlines(), start=1):
                if len(line) > MAX_LINE_LEN:
                    continue
                for term in tokenize(line):
                    postings.add((term, line_number))
            # index the filename too, so files are findable by name alone
            for term in tokenize(filepath):
                postings.add((term, 0))

            conn.executemany(
                "INSERT OR IGNORE INTO search_postings (term, document_id, line_number) VALUES (?, ?, ?)",
                [(term, doc_id, line_no) for term, line_no in postings],
            )
            indexed += 1

        for filepath in set(existing) - seen_paths:
            conn.execute("DELETE FROM search_documents WHERE id = ?", (existing[filepath][0],))

        conn.commit()
    finally:
        conn.close()
    return indexed


def _snippet(username: str, repo_name: str, branch: str, filepath: str, line_number: int) -> str:
    if line_number <= 0:
        return ""
    repo_path = REPOS_DIR / username / f"{repo_name}.git"
    try:
        content = git_utils.read_file(repo_path, branch, filepath)
    except git_utils.GitError:
        return ""
    lines = content.splitlines()
    idx = line_number - 1
    if 0 <= idx < len(lines):
        return lines[idx].strip()[:200]
    return ""


def search(owner_id: int, username: str, query: str, limit: int = 20) -> list[dict]:
    terms = sorted(set(tokenize(query)))
    if not terms:
        return []

    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in terms)

        total_docs = (
            conn.execute(
                "SELECT COUNT(*) AS c FROM search_documents WHERE owner_id = ?", (owner_id,)
            ).fetchone()["c"]
            or 1
        )

        df_rows = conn.execute(
            f"""
            SELECT p.term, COUNT(DISTINCT p.document_id) AS df
            FROM search_postings p
            JOIN search_documents d ON d.id = p.document_id
            WHERE d.owner_id = ? AND p.term IN ({placeholders})
            GROUP BY p.term
            """,
            (owner_id, *terms),
        ).fetchall()
        idf = {row["term"]: math.log((total_docs + 1) / (row["df"] + 1)) + 1 for row in df_rows}

        rows = conn.execute(
            f"""
            SELECT p.term, p.document_id, p.line_number, d.repo_name, d.filepath
            FROM search_postings p
            JOIN search_documents d ON d.id = p.document_id
            WHERE d.owner_id = ? AND p.term IN ({placeholders})
            """,
            (owner_id, *terms),
        ).fetchall()

        scores: dict[int, float] = {}
        matched_terms: dict[int, set] = {}
        best_line: dict[int, int] = {}
        doc_meta: dict[int, tuple] = {}

        for row in rows:
            doc_id = row["document_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + idf.get(row["term"], 0.0)
            matched_terms.setdefault(doc_id, set()).add(row["term"])
            doc_meta[doc_id] = (row["repo_name"], row["filepath"])
            line_no = row["line_number"]
            if line_no > 0 and (doc_id not in best_line or line_no < best_line[doc_id]):
                best_line[doc_id] = line_no

        ranked = sorted(
            scores.keys(), key=lambda d: (-len(matched_terms[d]), -scores[d], doc_meta[d][1])
        )[:limit]

        branch_cache: dict[str, str | None] = {}
        results = []
        for doc_id in ranked:
            repo_name, filepath = doc_meta[doc_id]
            if repo_name not in branch_cache:
                repo_path = REPOS_DIR / username / f"{repo_name}.git"
                branch_cache[repo_name] = git_utils.default_branch(repo_path)
            branch = branch_cache[repo_name] or "HEAD"
            line_number = best_line.get(doc_id, 0)
            results.append(
                {
                    "repo_name": repo_name,
                    "filepath": filepath,
                    "line_number": line_number,
                    "snippet": _snippet(username, repo_name, branch, filepath, line_number),
                    "score": round(scores[doc_id], 2),
                }
            )
        return results
    finally:
        conn.close()
