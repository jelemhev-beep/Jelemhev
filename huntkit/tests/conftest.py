import os
import tempfile

os.environ["HUNTKIT_DATA_DIR"] = tempfile.mkdtemp()

import pytest  # noqa: E402

from huntkit.db import get_connection, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM scope")
        conn.execute("DELETE FROM subdomains")
        conn.execute("DELETE FROM open_ports")
        conn.execute("DELETE FROM findings")
        conn.commit()
    finally:
        conn.close()
    yield
