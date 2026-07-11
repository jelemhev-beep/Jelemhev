import os
import sys
import tempfile
from pathlib import Path

os.environ["MONIA_DATA_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clean_brain(monkeypatch, tmp_path):
    """Each test gets its own second-cerveau directory so notes from one
    test can never leak into another."""
    brain_dir = tmp_path / "secondcerveau"
    monkeypatch.setattr("monia.secondcerveau.BRAIN_DIR", brain_dir)
    yield
