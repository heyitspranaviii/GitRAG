from __future__ import annotations

import click

from gitrag.core.config import get_settings
from gitrag.core.logging import setup_logging
from gitrag.core.pipeline import GitRAG


def _make_rag() -> GitRAG:
    settings = get_settings()
    setup_logging(level=settings.log_level, log_format="console")
    return GitRAG(settings)


@click.group()
def cli() -> None:
    """GitRAG — chat with any repo, any language, fully locally."""


@cli.command()
@click.argument("repo_path")
def ingest(repo_path: str) -> None:
    """Ingest a repository. Run once before chatting."""
    rag   = _make_rag()
    stats = rag.ingest(repo_path)
    click.echo(f"\nDone. {stats['chunks']} chunks from {stats['files']} files in {stats['elapsed_s']}s")
    click.echo("Now run:  gitrag chat")


@cli.command()
@click.option("--session", default="default", show_default=True)
def chat(session: str) -> None:
    """Interactive multi-turn chat with the ingested repo."""
    rag = _make_rag()
    if not rag.load():
        return
    click.echo("GitRAG ready. Ask anything. Ctrl+C to exit.\n")
    while True:
        try:
            q = input("You: ").strip()
            if not q:
                continue
            click.echo("Thinking...\n")
            click.echo(f"GitRAG:\n{rag.ask(q, session_id=session)}\n")
        except KeyboardInterrupt:
            click.echo("\nBye!")
            break


@cli.command()
@click.argument("question")
@click.option("--session", default="default", show_default=True)
def ask(question: str, session: str) -> None:
    """Ask a single question non-interactively."""
    rag = _make_rag()
    if rag.load():
        click.echo(rag.ask(question, session_id=session))
