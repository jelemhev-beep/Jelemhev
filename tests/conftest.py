import os
import shutil
import tempfile

os.environ["GITHOME_DATA_DIR"] = tempfile.mkdtemp()

import pytest  # noqa: E402

from app.config import REPOS_DIR  # noqa: E402
from app.db import get_connection, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    init_db()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM repositories")
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()
    if REPOS_DIR.exists():
        shutil.rmtree(REPOS_DIR)
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    yield
