from __future__ import annotations
from pathlib import Path
from gitrag.core.types import RawFile
from gitrag.core.logging import get_logger
from gitrag.ingest.language import get_language
from gitrag.ingest.filters import is_in_skip_dir, should_skip_file

logger = get_logger(__name__)

def load_repo(repo_path: str) -> list[RawFile]:
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo not found: {repo_path}")
    files: list[RawFile] = []
    lang_counts: dict[str, int] = {}
    for p in root.rglob("*"):
        if not p.is_file(): continue
        if is_in_skip_dir(p, root): continue
        if should_skip_file(p): continue
        lang = get_language(p.suffix)
        if lang is None: continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not content.strip(): continue
        files.append(RawFile(
            path=str(p.relative_to(root)),
            abs_path=str(p), language=lang, content=content,
        ))
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    logger.info("repo_loaded", file_count=len(files), breakdown=lang_counts)
    return files
