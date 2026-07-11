"""Persistent memory: notes and conversation logs stored as plain markdown
files under ~/.monia/secondcerveau/<projet>/, one folder per project.
Deliberately just files on disk -- no database, easy to browse, back up,
or push to a git repo (like GitHome) by hand.
"""

import re
import time
from pathlib import Path

from .config import BRAIN_DIR


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "note"


def save_note(project: str, title: str, content: str) -> Path:
    project_dir = BRAIN_DIR / project
    project_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = project_dir / f"{timestamp}_{_slugify(title)}.md"
    body = (
        f"# {title}\n\n"
        f"Projet: {project}\n"
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"{content}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def list_projects() -> list[str]:
    if not BRAIN_DIR.exists():
        return []
    return sorted(p.name for p in BRAIN_DIR.iterdir() if p.is_dir())


def list_notes(project: str) -> list[Path]:
    project_dir = BRAIN_DIR / project
    if not project_dir.exists():
        return []
    return sorted(project_dir.glob("*.md"))


def read_note(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def search(query: str, project: str | None = None) -> list[tuple[Path, str]]:
    """Case-insensitive search across note contents. Returns (path, first
    matching line) pairs."""
    if not BRAIN_DIR.exists():
        return []

    roots = [BRAIN_DIR / project] if project else [d for d in BRAIN_DIR.iterdir() if d.is_dir()]
    query_lower = query.lower()
    results = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            if query_lower not in text.lower():
                continue
            for line in text.splitlines():
                if query_lower in line.lower():
                    results.append((path, line.strip()))
                    break
    return results
