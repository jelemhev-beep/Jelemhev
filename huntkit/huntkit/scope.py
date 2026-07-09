"""Authorized-scope allowlist.

huntkit refuses to run any reconnaissance against a domain that hasn't been
explicitly added to scope first. This is a deliberate friction point: it
exists so the tool can never be pointed at a target by accident, and every
scan traces back to a conscious "I'm authorized to test this" decision.
"""

from .db import get_connection, init_db


class NotInScopeError(Exception):
    pass


def add(domain: str) -> None:
    init_db()
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO scope (domain) VALUES (?)", (domain.lower().strip(),))
        conn.commit()
    finally:
        conn.close()


def remove(domain: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM scope WHERE domain = ?", (domain.lower().strip(),))
        conn.commit()
    finally:
        conn.close()


def list_scope() -> list[str]:
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute("SELECT domain FROM scope ORDER BY domain").fetchall()
    finally:
        conn.close()
    return [row["domain"] for row in rows]


def is_in_scope(domain: str) -> bool:
    return domain.lower().strip() in set(list_scope())


def require_in_scope(domain: str) -> None:
    if not is_in_scope(domain):
        raise NotInScopeError(
            f"'{domain}' n'est pas dans le scope autorise. "
            f"Ajoute-le d'abord avec: huntkit scope add {domain}"
        )
