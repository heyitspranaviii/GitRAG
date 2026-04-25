from __future__ import annotations
from pathlib import Path

SKIP_DIRS: set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".chroma", ".mypy_cache", ".pytest_cache",
    "target", ".gradle", "vendor", "Pods", "bin", "obj",
    ".idea", ".vscode", "coverage", "site-packages",
}

MAX_FILE_BYTES: int = 500_000

def is_in_skip_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts[:-1]
        return any(p in SKIP_DIRS or p.startswith(".") for p in parts)
    except ValueError:
        return False

def should_skip_file(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    try:
        return path.stat().st_size > MAX_FILE_BYTES
    except OSError:
        return True
