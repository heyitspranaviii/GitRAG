from __future__ import annotations

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".mjs": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".java": "java", ".go": "go", ".rs": "rust",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp",
    ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby", ".php": "php",
    ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
    ".lua": "lua", ".r": "r", ".R": "r", ".sh": "bash",
}

def get_language(ext: str) -> str | None:
    return EXTENSION_TO_LANGUAGE.get(ext.lower())

def supported_extensions() -> set[str]:
    return set(EXTENSION_TO_LANGUAGE.keys())
