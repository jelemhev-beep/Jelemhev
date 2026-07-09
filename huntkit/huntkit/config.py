import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("HUNTKIT_DATA_DIR", "~/.huntkit")).expanduser().resolve()
DB_PATH = DATA_DIR / "huntkit.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
