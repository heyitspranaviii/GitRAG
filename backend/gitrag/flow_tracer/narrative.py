from __future__ import annotations

from gitrag.core.types import TraceFrame


class NarrativeAssembler:
    def assemble(self, frame: TraceFrame, query: str) -> str:
        lines = [f"## Execution trace — `{frame.symbol}`", f"Query: {query}", "---"]
        self._render(frame, lines, indent=0)
        return "\n".join(lines)

    def _render(self, frame: TraceFrame, lines: list, indent: int) -> None:
        pad    = "  " * indent
        marker = "↳ " if indent > 0 else ""
        node   = frame.node

        if frame.is_recursive_ref:
            lines.append(f"{pad}{marker}`{frame.symbol}` ← recursive call (already expanding above)")
            return

        loc = f"{node.file}:{node.start_line}-{node.end_line}"
        lines.append(f"{pad}{marker}### `{frame.symbol}` ({loc})")

        if frame.is_external:
            lines.append(f"{pad}  [External — source not available in repo]")
            return

        if node.docstring:
            lines.append(f"{pad}  **Purpose:** {node.docstring}")

        lines.append(f"{pad}  **Source:**")
        lines.append(f"{pad}  ```{node.language}")
        for src_line in node.raw_body.strip().splitlines():
            lines.append(f"{pad}  {src_line}")
        lines.append(f"{pad}  ```")

        if node.calls:
            calls_str = ", ".join(f"`{c}`" for c in node.calls[:10])
            lines.append(f"{pad}  **Calls:** {calls_str}")

        if frame.children:
            lines.append(f"{pad}  **Expanding callees:**")
            lines.append("")
            for child in frame.children:
                self._render(child, lines, indent + 1)
                lines.append("")

    def summary(self, frame: TraceFrame) -> str:
        order: list[str] = []
        seen:  set[str]  = set()
        self._collect(frame, order, seen)
        return " → ".join(order)

    def _collect(self, frame: TraceFrame, order: list, seen: set) -> None:
        if frame.symbol in seen or frame.is_recursive_ref:
            return
        seen.add(frame.symbol)
        order.append(frame.symbol)
        for child in frame.children:
            self._collect(child, order, seen)
