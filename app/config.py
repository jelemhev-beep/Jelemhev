import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

DATA_DIR = Path(os.environ.get("GITHOME_DATA_DIR", "./data")).resolve()
REPOS_DIR = DATA_DIR / "repos"
DB_PATH = DATA_DIR / "app.db"
SECRET_KEY_PATH = DATA_DIR / "secret_key"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


def get_secret_key() -> str:
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()
    key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(key)
    SECRET_KEY_PATH.chmod(0o600)
    return key
