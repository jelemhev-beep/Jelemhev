import sqlite3

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS scope (
    domain TEXT PRIMARY KEY,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subdomains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_domain TEXT NOT NULL,
    hostname TEXT NOT NULL,
    ip TEXT,
    source TEXT NOT NULL,
    first_seen TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(root_domain, hostname)
);

CREATE TABLE IF NOT EXISTS open_ports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    port INTEGER NOT NULL,
    banner TEXT DEFAULT '',
    found_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(hostname, port)
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_domain TEXT NOT NULL,
    hostname TEXT NOT NULL,
    check_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT DEFAULT '',
    found_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(hostname, check_name, title)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
