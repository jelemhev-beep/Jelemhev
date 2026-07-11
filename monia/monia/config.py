import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("MONIA_DATA_DIR", "~/.monia")).expanduser()
BRAIN_DIR = DATA_DIR / "secondcerveau"

DATA_DIR.mkdir(parents=True, exist_ok=True)
