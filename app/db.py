import sqlite3

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(owner_id, name)
);

CREATE TABLE IF NOT EXISTS search_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_name TEXT NOT NULL,
    filepath TEXT NOT NULL,
    blob_sha TEXT NOT NULL,
    line_count INTEGER NOT NULL DEFAULT 0,
    indexed_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(owner_id, repo_name, filepath)
);

CREATE TABLE IF NOT EXISTS search_postings (
    term TEXT NOT NULL,
    document_id INTEGER NOT NULL REFERENCES search_documents(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    UNIQUE(term, document_id, line_number)
);

CREATE INDEX IF NOT EXISTS idx_postings_term ON search_postings(term);
CREATE INDEX IF NOT EXISTS idx_postings_doc ON search_postings(document_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
