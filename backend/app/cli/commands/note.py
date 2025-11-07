"""Note management CLI commands."""

import json
from pathlib import Path
from typing import List, Optional

import click

from backend.app.services.note_file_service import NoteFileService


@click.group(name="note")
def note_group():
    """Note management commands."""
    pass


@note_group.command(name="create")
@click.option("--title", required=True, help="Note title")
@click.option("--content", required=True, help="Note content")
@click.option("--file-path", help="File path (relative to notes directory)")
@click.option("--tags", help="Comma-separated tags")
def create_note(title, content, file_path, tags):
    """Create a new note."""
    note_service = NoteFileService()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    try:
        note_path = note_service.create_note(
            title=title, content=content, file_path=file_path, tags=tag_list
        )
        click.echo(f"✓ Note created: {note_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="list")
@click.option("--subdirectory", help="Subdirectory to list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def list_notes(subdirectory, json_output):
    """List all notes."""
    note_service = NoteFileService()

    try:
        notes = note_service.list_notes(subdirectory=subdirectory)

        if not notes:
            click.echo("No notes found.")
            return

        if json_output:
            notes_list = [str(note) for note in notes]
            click.echo(json.dumps(notes_list, indent=2))
        else:
            click.echo(f"Found {len(notes)} notes:\n")
            for note_path in sorted(notes):
                click.echo(f"  {note_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="show")
@click.argument("file_path", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_note(file_path, json_output):
    """Show a note's content."""
    note_service = NoteFileService()

    try:
        title, frontmatter, content = note_service.read_note(file_path)

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "title": title,
                        "file_path": file_path,
                        "frontmatter": frontmatter,
                        "content": content,
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            click.echo(f"Title: {title}")
            click.echo(f"Path: {file_path}\n")
            if frontmatter:
                click.echo("Frontmatter:")
                for key, value in frontmatter.items():
                    click.echo(f"  {key}: {value}")
                click.echo()
            click.echo("Content:")
            click.echo("-" * 60)
            click.echo(content)

    except FileNotFoundError:
        click.echo(f"Error: Note '{file_path}' not found.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="update")
@click.argument("file_path", type=str)
@click.option("--content", help="New content")
@click.option("--title", help="New title")
@click.option("--tags", help="Comma-separated tags")
def update_note(file_path, content, title, tags):
    """Update a note."""
    note_service = NoteFileService()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    try:
        note_path = note_service.update_note(
            file_path=file_path, content=content, title=title, tags=tag_list
        )
        click.echo(f"✓ Note updated: {note_path}")
    except FileNotFoundError:
        click.echo(f"Error: Note '{file_path}' not found.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="delete")
@click.argument("file_path", type=str)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_note(file_path, yes):
    """Delete a note."""
    note_service = NoteFileService()

    if not yes:
        click.confirm(f"Delete note '{file_path}'?", abort=True)

    try:
        deleted = note_service.delete_note(file_path)
        if deleted:
            click.echo(f"✓ Note '{file_path}' deleted successfully.")
        else:
            click.echo(f"Note '{file_path}' not found.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="links")
@click.argument("file_path", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_links(file_path, json_output):
    """Extract and show links from a note."""
    note_service = NoteFileService()

    try:
        metadata = note_service.get_note_metadata(file_path)
        links = metadata.links

        if json_output:
            click.echo(json.dumps({"file_path": file_path, "links": links}, indent=2))
        else:
            if links:
                click.echo(f"Found {len(links)} links in '{file_path}':\n")
                for link in links:
                    click.echo(f"  [[{link}]]")
            else:
                click.echo(f"No links found in '{file_path}'.")

    except FileNotFoundError:
        click.echo(f"Error: Note '{file_path}' not found.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="vectorize")
@click.argument("file_path", type=str)
@click.option("--all", is_flag=True, help="Vectorize all notes")
def vectorize_note(file_path, all):
    """Vectorize a note (placeholder - not yet implemented)."""
    if all:
        click.echo("Batch vectorization feature not yet implemented.")
        click.echo("This will vectorize all notes in the notes directory.")
    else:
        click.echo(f"Note vectorization feature not yet implemented.")
        click.echo(f"This will vectorize note '{file_path}' and store it in the vector database.")

