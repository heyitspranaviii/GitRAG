from __future__ import annotations


def format_chunks(chunks: list[dict]) -> str:
    """Format retrieved chunks as numbered fenced code blocks."""
    parts = []
    for i, c in enumerate(chunks, 1):
        m   = c.get("meta", {})
        loc = f"{m.get('file','?')}:{m.get('start_line','?')}-{m.get('end_line','?')}"
        parts.append(
            f"### Chunk {i}: `{m.get('symbol','?')}` ({loc})\n"
            f"```{m.get('language','')}\n{c['text']}\n```"
        )
    return "\n\n".join(parts)


def trim_to_limit(text: str, limit: int = 6000) -> str:
    """Hard-trim context to approximately `limit` characters."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[... context trimmed to fit token limit ...]"


def build_context(
    chunks:         list[dict],
    flow_narrative: str = "",
    semgrep_str:    str = "",
    memory_str:     str = "",
    limit:          int = 6000,
) -> str:
    """
    Assemble all context sections in priority order and trim to limit.
    Order: retrieved code → flow trace → security findings → memory
    """
    parts = []
    if chunks:         parts.append("## Retrieved code context\n" + format_chunks(chunks))
    if flow_narrative: parts.append("## Execution trace\n" + flow_narrative)
    if semgrep_str:    parts.append("## Security findings\n" + semgrep_str)
    if memory_str:     parts.append(memory_str)
    combined = "\n\n---\n\n".join(parts)
    return trim_to_limit(combined, limit)
