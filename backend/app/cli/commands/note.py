"""Note management CLI commands."""

import json
from pathlib import Path
from typing import List, Optional

import click

from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.note_vectorization_service import NoteVectorizationService


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
@click.argument("file_path", type=str, required=False)
@click.option("--from", "from_note_id", help="Show links from a note (by note_id)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_links(file_path, from_note_id, json_output):
    """Extract and show links from a note or show linked notes."""
    note_service = NoteFileService()
    note_metadata_service = NoteMetadataService()

    try:
        if from_note_id:
            # Show linked notes from a note_id
            linked_notes = note_metadata_service.get_linked_notes(from_note_id)
            backlinks = note_metadata_service.get_backlinks(from_note_id)

            if json_output:
                click.echo(
                    json.dumps(
                        {
                            "note_id": from_note_id,
                            "linked_notes": [
                                {
                                    "note_id": note.note_id,
                                    "title": note.title,
                                    "file_path": note.file_path,
                                }
                                for note in linked_notes
                            ],
                            "backlinks": [
                                {
                                    "note_id": note.note_id,
                                    "title": note.title,
                                    "file_path": note.file_path,
                                }
                                for note in backlinks
                            ],
                        },
                        indent=2,
                        default=str,
                    )
                )
            else:
                click.echo(f"Links for note '{from_note_id}':\n")
                if linked_notes:
                    click.echo(f"Outgoing links ({len(linked_notes)}):")
                    for note in linked_notes:
                        click.echo(f"  → {note.title} ({note.file_path})")
                    click.echo()
                else:
                    click.echo("No outgoing links.\n")

                if backlinks:
                    click.echo(f"Backlinks ({len(backlinks)}):")
                    for note in backlinks:
                        click.echo(f"  ← {note.title} ({note.file_path})")
                else:
                    click.echo("No backlinks.")
        else:
            # Show links from a file_path
            if not file_path:
                click.echo("Error: file_path is required when --from is not used.", err=True)
                raise click.Abort()

            metadata = note_service.get_note_metadata(file_path)
            links = metadata.links

            # Also get linked notes from SQLite if available
            note_id = str(file_path).replace("\\", "/").replace(".md", "")
            linked_notes = note_metadata_service.get_linked_notes(note_id)

            if json_output:
                click.echo(
                    json.dumps(
                        {
                            "file_path": file_path,
                            "links": links,
                            "linked_notes": [
                                {
                                    "note_id": note.note_id,
                                    "title": note.title,
                                    "file_path": note.file_path,
                                }
                                for note in linked_notes
                            ],
                        },
                        indent=2,
                        default=str,
                    )
                )
            else:
                if links:
                    click.echo(f"Found {len(links)} links in '{file_path}':\n")
                    for link in links:
                        click.echo(f"  [[{link}]]")
                    click.echo()

                if linked_notes:
                    click.echo(f"Resolved linked notes ({len(linked_notes)}):")
                    for note in linked_notes:
                        click.echo(f"  → {note.title} ({note.file_path})")
                elif links:
                    click.echo("(No resolved linked notes found)")
                else:
                    click.echo(f"No links found in '{file_path}'.")

    except FileNotFoundError:
        click.echo(f"Error: Note '{file_path}' not found.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="update-metadata")
@click.option("--all", is_flag=True, help="Update metadata for all notes")
@click.argument("file_path", type=str, required=False)
def update_note_metadata(file_path, all):
    """Update note metadata in SQLite (tags, links) without re-vectorizing."""
    vectorization_service = NoteVectorizationService()

    try:
        if all:
            # Batch metadata update
            click.echo("Starting batch metadata update for all notes...")
            updated_count, error_count = vectorization_service.update_all_notes_metadata()
            click.echo(f"\n✓ Metadata update complete:")
            click.echo(f"  - Updated: {updated_count}")
            click.echo(f"  - Errors: {error_count}")
        else:
            if not file_path:
                click.echo("Error: file_path is required when --all is not used.", err=True)
                raise click.Abort()

            # Single note metadata update
            click.echo(f"Updating metadata for note: {file_path}")
            metadata = vectorization_service.update_note_metadata(file_path)
            click.echo(f"✓ Note metadata updated successfully:")
            click.echo(f"  - Note ID: {metadata.note_id}")
            click.echo(f"  - Title: {metadata.title}")
            click.echo(f"  - Tags: {', '.join(metadata.tags) if metadata.tags else 'None'}")
            click.echo(f"  - Links: {len(metadata.links)} links")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="vectorize")
@click.argument("file_path", type=str, required=False)
@click.option("--all", is_flag=True, help="Vectorize all notes")
@click.option("--force", is_flag=True, help="Force re-vectorization even if already vectorized")
@click.option("--incremental/--no-incremental", default=True, help="Only vectorize new notes (default: True)")
def vectorize_note(file_path, all, force, incremental):
    """Vectorize a note or all notes."""
    vectorization_service = NoteVectorizationService()

    try:
        if all:
            # Batch vectorization
            click.echo("Starting batch vectorization of all notes...")
            vectorized_count, skipped_count = vectorization_service.vectorize_all_notes(
                force=force, incremental=incremental
            )
            click.echo(f"\n✓ Vectorization complete:")
            click.echo(f"  - Vectorized: {vectorized_count}")
            click.echo(f"  - Skipped: {skipped_count}")
        else:
            if not file_path:
                click.echo("Error: file_path is required when --all is not used.", err=True)
                raise click.Abort()

            # Single note vectorization
            click.echo(f"Vectorizing note: {file_path}")
            metadata = vectorization_service.vectorize_note(file_path, force=force)
            click.echo(f"✓ Note vectorized successfully:")
            click.echo(f"  - Doc ID: {metadata.doc_id}")
            click.echo(f"  - Title: {metadata.title}")
            click.echo(f"  - Chunks: {metadata.chunk_total or 0}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@note_group.command(name="search")
@click.argument("query", type=str, required=False)
@click.option("--limit", default=10, help="Maximum number of results")
@click.option("--tag", help="Filter by tag (can be used without query)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def search_notes(query, limit, tag, json_output):
    """Search notes by semantic similarity or filter by tag."""
    vectorization_service = NoteVectorizationService()

    # Validate: at least one of query or tag must be provided
    if not query and not tag:
        click.echo("Error: At least one of 'query' or '--tag' must be provided.", err=True)
        raise click.Abort()

    try:
        results = vectorization_service.search_notes(query=query, limit=limit, tag=tag)

        if not results:
            click.echo("No matching notes found.")
            return

        if json_output:
            click.echo(json.dumps(results, indent=2, default=str))
        else:
            click.echo(f"Found {len(results)} matching notes:\n")
            for i, result in enumerate(results, 1):
                similarity_str = f" (similarity: {result['similarity']:.3f})" if result.get('similarity') else ""
                click.echo(f"{i}. {result['title']}{similarity_str}")
                click.echo(f"   Path: {result['file_path']}")
                if result.get("tags"):
                    tags_str = ", ".join(result["tags"])
                    click.echo(f"   Tags: {tags_str}")
                if result.get("content"):
                    click.echo(f"   Content preview: {result['content'][:100]}...")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

