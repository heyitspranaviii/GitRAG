from __future__ import annotations

from gitrag.core.types import Chunk, Finding


def tag_chunks(
    chunks:   list[Chunk],
    findings: list[Finding],
) -> dict[str, list[str]]:
    """Match findings to chunks by file + line overlap. Returns chunk_id → [rule_ids]."""
    tags: dict[str, list[str]] = {}
    for finding in findings:
        for chunk in chunks:
            file_match = (
                chunk.file == finding.file
                or chunk.file.endswith(finding.file)
                or finding.file.endswith(chunk.file)
            )
            if not file_match:
                continue
            if finding.start_line <= chunk.end_line and finding.end_line >= chunk.start_line:
                tags.setdefault(chunk.chunk_id, []).append(finding.rule_id)
    return tags


def format_findings_for_prompt(findings: list[Finding]) -> str:
    """Format findings as a bulleted list for the LLM security prompt."""
    if not findings:
        return ""
    lines = []
    for f in findings:
        lines.append(
            f"- [{f.severity.value}] **{f.rule_id}**\n"
            f"  File: `{f.file}` line {f.start_line}\n"
            f"  Issue: {f.message}\n"
            f"  Code: `{f.snippet}`"
        )
    return "\n".join(lines)
