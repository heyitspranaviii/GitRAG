from __future__ import annotations
import sqlite3
from pathlib import Path
from gitrag.core.types import Turn

class Memory:
    def __init__(self, session_id: str = "default", memory_path: str = ".memory") -> None:
        Path(memory_path).mkdir(parents=True, exist_ok=True)
        self.db_path = str(Path(memory_path) / f"{session_id}.db")
        with sqlite3.connect(self.db_path) as con:
            con.execute("CREATE TABLE IF NOT EXISTS turns (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL)")

    def add(self, role: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute("INSERT INTO turns (role, content) VALUES (?, ?)", (role, content))

    def get_history(self, last_n: int = 6) -> list[Turn]:
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute("SELECT role, content FROM turns ORDER BY id DESC LIMIT ?", (last_n,)).fetchall()
        return [Turn(role=r[0], content=r[1]) for r in reversed(rows)]

    def format_for_prompt(self, last_n: int = 6) -> str:
        turns = self.get_history(last_n)
        if not turns: return ""
        return "## Conversation history\n" + "\n".join(f"{t.role.upper()}: {t.content}" for t in turns)

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute("DELETE FROM turns")

    def turn_count(self) -> int:
        with sqlite3.connect(self.db_path) as con:
            return con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
