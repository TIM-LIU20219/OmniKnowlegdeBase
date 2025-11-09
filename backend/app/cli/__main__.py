"""Main CLI entry point for OmniKnowledgeBase."""

import sys
from pathlib import Path

import click

# Lazy import commands to avoid slow imports at startup
# Commands will be imported only when needed
from backend.app.utils.filesystem import ensure_directories
from backend.app.utils.logging_config import setup_logging

# Initialize directories and logging
ensure_directories()
setup_logging()


@click.group()
@click.version_option(version="0.1.0", prog_name="OmniKnowledgeBase CLI")
def cli():
    """
    OmniKnowledgeBase CLI - Unified command-line interface for document processing,
    note management, RAG Q&A, and vector storage.
    """
    pass


def _register_commands():
    """Lazy register command groups to avoid slow imports at startup."""
    from backend.app.cli.commands import document, index, note, rag, vector

    cli.add_command(document.document_group)
    cli.add_command(index.index_group)
    cli.add_command(note.note_group)
    cli.add_command(rag.rag_group)
    cli.add_command(vector.vector_group)


def main():
    """Entry point for CLI."""
    _register_commands()
    cli()


if __name__ == "__main__":
    main()

