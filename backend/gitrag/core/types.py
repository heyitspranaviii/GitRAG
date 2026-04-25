from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR   = "ERROR"
    WARNING = "WARNING"
    INFO    = "INFO"


class ChunkType(str, Enum):
    FUNCTION = "function"
    CLASS    = "class"
    MODULE   = "module"


class IntentType(str, Enum):
    FLOW      = "flow"
    SECURITY  = "security"
    MULTI_HOP = "multi_hop"
    GENERAL   = "general"


# ── Ingestion ─────────────────────────────────────────────────────────────────

@dataclass
class RawFile:
    path:     str
    abs_path: str
    language: str
    content:  str


# ── Chunking ──────────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    chunk_id:    str
    symbol_name: str
    file:        str
    language:    str
    start_line:  int
    end_line:    int
    raw_text:    str
    docstring:   str       = ""
    chunk_type:  ChunkType = ChunkType.FUNCTION

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id":    self.chunk_id,
            "symbol_name": self.symbol_name,
            "file":        self.file,
            "language":    self.language,
            "start_line":  self.start_line,
            "end_line":    self.end_line,
            "chunk_type":  self.chunk_type.value,
        }


# ── Retrieval ─────────────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    text:         str
    meta:         dict[str, Any]
    score:        float
    chunk_id:     str
    rerank_score: float = 0.0


# ── Intent ────────────────────────────────────────────────────────────────────

@dataclass
class Intent:
    type:         IntentType = IntentType.GENERAL
    is_flow:      bool       = False
    is_security:  bool       = False
    is_multi_hop: bool       = False
    flow_symbol:  str        = ""
    raw_query:    str        = ""
    rewritten:    str        = ""


# ── Memory ────────────────────────────────────────────────────────────────────

@dataclass
class Turn:
    role:    str
    content: str


# ── Semgrep ───────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    rule_id:    str
    file:       str
    start_line: int
    end_line:   int
    message:    str
    severity:   Severity
    snippet:    str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id":    self.rule_id,
            "file":       self.file,
            "start_line": self.start_line,
            "message":    self.message,
            "severity":   self.severity.value,
            "snippet":    self.snippet,
        }


# ── Flow tracer ───────────────────────────────────────────────────────────────

@dataclass
class CallNode:
    symbol:      str
    file:        str
    start_line:  int
    end_line:    int
    language:    str
    raw_body:    str
    docstring:   str        = ""
    calls:       list[str]  = field(default_factory=list)
    is_external: bool       = False


@dataclass
class TraceFrame:
    depth:            int
    symbol:           str
    node:             CallNode
    children:         list[TraceFrame] = field(default_factory=list)
    is_recursive_ref: bool             = False
    is_external:      bool             = False


# ── Evaluation ────────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    precision_at_k: float
    mrr:            float
    ndcg:           float
    faithfulness:   float

    def to_dict(self) -> dict[str, float]:
        return {
            "precision_at_k": self.precision_at_k,
            "mrr":            self.mrr,
            "ndcg":           self.ndcg,
            "faithfulness":   self.faithfulness,
        }
