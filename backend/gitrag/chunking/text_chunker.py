from __future__ import annotations
import re
from gitrag.core.types import Chunk, ChunkType, RawFile

def _make_id(file: str, start: int) -> str:
    return re.sub(r"[^\w]", "_", file) + f"__block_{start}"

def chunk_by_window(raw_file: RawFile, window: int = 60, overlap: int = 10) -> list[Chunk]:
    lines = raw_file.content.splitlines()
    chunks: list[Chunk] = []
    step = max(1, window - overlap)
    for i in range(0, max(1, len(lines) - overlap), step):
        block = lines[i:i + window]
        if not block: continue
        chunks.append(Chunk(
            chunk_id=_make_id(raw_file.path, i + 1),
            symbol_name=f"block_{i+1}",
            file=raw_file.path,
            language=raw_file.language,
            start_line=i + 1,
            end_line=i + len(block),
            raw_text="\n".join(block),
            chunk_type=ChunkType.MODULE,
        ))
    return chunks
