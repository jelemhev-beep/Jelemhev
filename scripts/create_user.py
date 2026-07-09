#!/usr/bin/env python3
"""Create an additional user account (admin utility, run outside the web UI).

Usage: python scripts/create_user.py <username>
Prompts for a password (hidden input).
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_connection, init_db  # noqa: E402
from app.security import hash_password  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    username = sys.argv[1]
    password = getpass.getpass("Mot de passe: ")
    confirm = getpass.getpass("Confirme le mot de passe: ")
    if password != confirm:
        print("Les mots de passe ne correspondent pas.")
        return 1
    if len(password) < 8:
        print("Le mot de passe doit faire au moins 8 caracteres.")
        return 1

    init_db()
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            print(f"L'utilisateur '{username}' existe deja.")
            return 1
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
    finally:
        conn.close()
    print(f"Utilisateur '{username}' cree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
