"""Service for managing note metadata in SQLite database."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.models.metadata import NoteMetadata
from backend.app.utils.filesystem import BASE_DIR, ensure_directories

logger = logging.getLogger(__name__)

# Database path
DB_DIR = BASE_DIR / "backend" / "app" / "db"
DB_PATH = DB_DIR / "notes.db"


class NoteMetadataService:
    """Service for managing note metadata in SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize note metadata service.

        Args:
            db_path: Optional path to SQLite database. If None, uses default.
        """
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"Initialized NoteMetadataService with database: {self.db_path}")

    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Notes metadata table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    tags TEXT,  -- JSON array
                    links TEXT,  -- JSON array
                    frontmatter TEXT,  -- JSON object
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Note links relationship table (for bidirectional links)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS note_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_note_id TEXT NOT NULL,
                    target_note_id TEXT NOT NULL,
                    link_name TEXT,  -- Store original link name for unresolved links
                    FOREIGN KEY (source_note_id) REFERENCES notes(note_id),
                    FOREIGN KEY (target_note_id) REFERENCES notes(note_id),
                    UNIQUE(source_note_id, target_note_id)
                )
            """
            )
            
            # Unresolved links table (for links to notes that don't exist yet)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS unresolved_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_note_id TEXT NOT NULL,
                    link_name TEXT NOT NULL,
                    FOREIGN KEY (source_note_id) REFERENCES notes(note_id),
                    UNIQUE(source_note_id, link_name)
                )
            """
            )

            # Tag index table (for efficient tag queries)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS note_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT NOT NULL,
                    note_id TEXT NOT NULL,
                    FOREIGN KEY (note_id) REFERENCES notes(note_id),
                    UNIQUE(tag, note_id)
                )
            """
            )

            # Create indexes for better query performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_note_links_source ON note_links(source_note_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(target_note_id)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_tags_note ON note_tags(note_id)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unresolved_links_source ON unresolved_links(source_note_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unresolved_links_name ON unresolved_links(link_name)"
            )

            conn.commit()
            logger.debug("Database tables initialized")

    def create_note_metadata(self, note_metadata: NoteMetadata) -> NoteMetadata:
        """
        Create or update note metadata in database.

        Args:
            note_metadata: NoteMetadata instance

        Returns:
            Created NoteMetadata instance
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Custom JSON encoder for datetime objects
            def json_serializer(obj):
                """Custom JSON serializer for objects not serializable by default json code."""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            # Insert or replace note metadata
            cursor.execute(
                """
                INSERT OR REPLACE INTO notes (
                    note_id, title, file_path, tags, links, frontmatter,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    note_metadata.note_id,
                    note_metadata.title,
                    note_metadata.file_path,
                    json.dumps(note_metadata.tags, ensure_ascii=False, default=json_serializer),
                    json.dumps(note_metadata.links, ensure_ascii=False, default=json_serializer),
                    json.dumps(note_metadata.frontmatter, ensure_ascii=False, default=json_serializer),
                    note_metadata.created_at.isoformat(),
                    note_metadata.updated_at.isoformat(),
                ),
            )

            # Update tag index
            cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_metadata.note_id,))
            for tag in note_metadata.tags:
                cursor.execute(
                    "INSERT OR IGNORE INTO note_tags (tag, note_id) VALUES (?, ?)",
                    (tag, note_metadata.note_id),
                )

            # Update links relationship
            cursor.execute(
                "DELETE FROM note_links WHERE source_note_id = ?",
                (note_metadata.note_id,),
            )
            cursor.execute(
                "DELETE FROM unresolved_links WHERE source_note_id = ?",
                (note_metadata.note_id,),
            )
            
            for link in note_metadata.links:
                # Try to find target note by link name (with improved matching)
                target_note_id = self._find_note_id_by_name(link)
                if target_note_id:
                    # Found matching note, create link relationship
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO note_links (source_note_id, target_note_id, link_name)
                        VALUES (?, ?, ?)
                    """,
                        (note_metadata.note_id, target_note_id, link),
                    )
                    logger.debug(f"Created link: {note_metadata.note_id} -> {target_note_id} ({link})")
                else:
                    # Link target not found, store as unresolved link
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO unresolved_links (source_note_id, link_name)
                        VALUES (?, ?)
                    """,
                        (note_metadata.note_id, link),
                    )
                    logger.debug(f"Stored unresolved link: {link} (from {note_metadata.note_id})")

            conn.commit()
            logger.debug(f"Created/updated note metadata: {note_metadata.note_id}")
            return note_metadata

    def get_note_metadata(self, note_id: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by note_id.

        Args:
            note_id: Note identifier

        Returns:
            NoteMetadata instance or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notes WHERE note_id = ?", (note_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_note_metadata(row)

    def get_note_metadata_by_path(self, file_path: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by file path.

        Args:
            file_path: File path relative to notes directory

        Returns:
            NoteMetadata instance or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notes WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_note_metadata(row)

    def get_notes_by_tag(self, tag: str) -> List[NoteMetadata]:
        """
        Get all notes with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of NoteMetadata instances
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT n.* FROM notes n
                INNER JOIN note_tags nt ON n.note_id = nt.note_id
                WHERE nt.tag = ?
                ORDER BY n.updated_at DESC
            """,
                (tag,),
            )

            rows = cursor.fetchall()
            return [self._row_to_note_metadata(row) for row in rows]

    def get_linked_notes(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes linked from a given note.

        Args:
            note_id: Source note identifier

        Returns:
            List of linked NoteMetadata instances
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT n.* FROM notes n
                INNER JOIN note_links nl ON n.note_id = nl.target_note_id
                WHERE nl.source_note_id = ?
                ORDER BY n.title
            """,
                (note_id,),
            )

            rows = cursor.fetchall()
            return [self._row_to_note_metadata(row) for row in rows]

    def get_backlinks(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes that link to a given note (backlinks).

        Args:
            note_id: Target note identifier

        Returns:
            List of NoteMetadata instances that link to this note
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT n.* FROM notes n
                INNER JOIN note_links nl ON n.note_id = nl.source_note_id
                WHERE nl.target_note_id = ?
                ORDER BY n.title
            """,
                (note_id,),
            )

            rows = cursor.fetchall()
            return [self._row_to_note_metadata(row) for row in rows]

    def delete_note_metadata(self, note_id: str) -> bool:
        """
        Delete note metadata and related records.

        Args:
            note_id: Note identifier

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete from related tables first
            cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
            cursor.execute("DELETE FROM note_links WHERE source_note_id = ?", (note_id,))
            cursor.execute("DELETE FROM note_links WHERE target_note_id = ?", (note_id,))

            # Delete note metadata
            cursor.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            if deleted:
                logger.debug(f"Deleted note metadata: {note_id}")
            return deleted

    def list_all_notes(self) -> List[NoteMetadata]:
        """
        List all notes in database.

        Returns:
            List of NoteMetadata instances
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_note_metadata(row) for row in rows]

    def _find_note_id_by_name(self, link_name: str) -> Optional[str]:
        """
        Find note_id by link name (note title or file path stem).
        
        Uses multiple matching strategies:
        1. Exact title match (case-insensitive)
        2. File path stem match
        3. Title contains link name (fuzzy match)
        4. Link name contains title (fuzzy match)

        Args:
            link_name: Link name from [[note-name]]

        Returns:
            Note ID if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Strategy 1: Exact title match (case-insensitive)
            cursor.execute(
                "SELECT note_id FROM notes WHERE LOWER(title) = LOWER(?)",
                (link_name,),
            )
            row = cursor.fetchone()
            if row:
                return row[0]

            # Strategy 2: File path stem match
            cursor.execute(
                "SELECT note_id FROM notes WHERE file_path LIKE ?",
                (f"%{link_name}.md",),
            )
            row = cursor.fetchone()
            if row:
                return row[0]

            # Strategy 3: Title contains link name (fuzzy match)
            cursor.execute(
                "SELECT note_id FROM notes WHERE title LIKE ?",
                (f"%{link_name}%",),
            )
            row = cursor.fetchone()
            if row:
                return row[0]

            # Strategy 4: Link name contains title (fuzzy match)
            # This is more expensive, so we do it last
            cursor.execute("SELECT note_id, title FROM notes")
            all_notes = cursor.fetchall()
            for note_id, title in all_notes:
                if title in link_name or link_name in title:
                    return note_id

            return None

    def resolve_unresolved_links(self, new_note_id: str, new_note_title: str) -> int:
        """
        Try to resolve unresolved links when a new note is created.
        
        Args:
            new_note_id: ID of the newly created note
            new_note_title: Title of the newly created note
            
        Returns:
            Number of links resolved
        """
        resolved_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Find unresolved links that might match this new note
            cursor.execute(
                "SELECT source_note_id, link_name FROM unresolved_links"
            )
            unresolved = cursor.fetchall()
            
            for source_note_id, link_name in unresolved:
                # Check if the new note matches this unresolved link
                if (link_name == new_note_title or 
                    link_name in new_note_title or 
                    new_note_title in link_name):
                    # Resolve the link
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO note_links (source_note_id, target_note_id, link_name)
                        VALUES (?, ?, ?)
                    """,
                        (source_note_id, new_note_id, link_name),
                    )
                    # Remove from unresolved links
                    cursor.execute(
                        "DELETE FROM unresolved_links WHERE source_note_id = ? AND link_name = ?",
                        (source_note_id, link_name),
                    )
                    resolved_count += 1
                    logger.info(f"Resolved link: {source_note_id} -> {new_note_id} ({link_name})")
            
            conn.commit()
        
        return resolved_count

    def get_unresolved_links(self, note_id: Optional[str] = None) -> List[tuple]:
        """
        Get unresolved links.
        
        Args:
            note_id: Optional note ID to filter by
            
        Returns:
            List of (source_note_id, link_name) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if note_id:
                cursor.execute(
                    "SELECT source_note_id, link_name FROM unresolved_links WHERE source_note_id = ?",
                    (note_id,),
                )
            else:
                cursor.execute("SELECT source_note_id, link_name FROM unresolved_links")
            
            return cursor.fetchall()

    def _row_to_note_metadata(self, row: sqlite3.Row) -> NoteMetadata:
        """
        Convert database row to NoteMetadata instance.

        Args:
            row: SQLite row object

        Returns:
            NoteMetadata instance
        """
        return NoteMetadata(
            note_id=row["note_id"],
            title=row["title"],
            file_path=row["file_path"],
            tags=json.loads(row["tags"] or "[]"),
            links=json.loads(row["links"] or "[]"),
            frontmatter=json.loads(row["frontmatter"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

