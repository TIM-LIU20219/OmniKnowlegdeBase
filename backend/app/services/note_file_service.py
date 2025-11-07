"""Note file management service for Obsidian-style notes."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from backend.app.models.metadata import NoteMetadata
from backend.app.utils.filesystem import NOTES_DIR, ensure_directories

logger = logging.getLogger(__name__)


class NoteFileService:
    """Service for managing Obsidian-style note files."""

    def __init__(self, notes_directory: Optional[Path] = None):
        """
        Initialize note file service.

        Args:
            notes_directory: Directory containing notes. If None, uses default.
        """
        self.notes_directory = notes_directory or NOTES_DIR
        ensure_directories()
        logger.info(f"Initialized NoteFileService with directory: {self.notes_directory}")

    def create_note(
        self,
        title: str,
        content: str,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        frontmatter: Optional[Dict] = None,
    ) -> Path:
        """
        Create a new note file.

        Args:
            title: Note title
            content: Note content (markdown)
            file_path: Optional relative path from notes directory. If None, uses title.
            tags: Optional list of tags
            frontmatter: Optional frontmatter dictionary

        Returns:
            Path to created note file
        """
        # Generate file path if not provided
        if file_path is None:
            # Sanitize title for filename
            safe_title = self._sanitize_filename(title)
            file_path = f"{safe_title}.md"

        note_path = self.notes_directory / file_path
        note_path.parent.mkdir(parents=True, exist_ok=True)

        # Build frontmatter
        frontmatter_dict = frontmatter or {}
        frontmatter_dict["title"] = title
        frontmatter_dict["created_at"] = datetime.now().isoformat()
        frontmatter_dict["updated_at"] = datetime.now().isoformat()
        if tags:
            frontmatter_dict["tags"] = tags

        # Write note file
        note_content = self._build_note_content(frontmatter_dict, content)
        note_path.write_text(note_content, encoding="utf-8")

        logger.info(f"Created note: {note_path}")
        return note_path

    def read_note(self, file_path: str) -> Tuple[str, Dict, str]:
        """
        Read a note file and parse frontmatter and content.

        Args:
            file_path: Relative path from notes directory

        Returns:
            Tuple of (title, frontmatter_dict, content)
        """
        note_path = self.notes_directory / file_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        content = note_path.read_text(encoding="utf-8")
        frontmatter, body = self._parse_frontmatter(content)

        title = frontmatter.get("title", self._extract_title_from_path(file_path))
        return title, frontmatter, body

    def update_note(
        self,
        file_path: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        frontmatter: Optional[Dict] = None,
    ) -> Path:
        """
        Update an existing note.

        Args:
            file_path: Relative path from notes directory
            content: Optional new content
            title: Optional new title
            tags: Optional new tags
            frontmatter: Optional frontmatter updates (merged with existing)

        Returns:
            Path to updated note file
        """
        note_path = self.notes_directory / file_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        # Read existing note
        existing_title, existing_frontmatter, existing_content = self.read_note(file_path)

        # Update content
        new_content = content if content is not None else existing_content

        # Update frontmatter
        updated_frontmatter = existing_frontmatter.copy()
        if title:
            updated_frontmatter["title"] = title
        if tags is not None:
            updated_frontmatter["tags"] = tags
        if frontmatter:
            updated_frontmatter.update(frontmatter)
        updated_frontmatter["updated_at"] = datetime.now().isoformat()

        # Write updated note
        note_content = self._build_note_content(updated_frontmatter, new_content)
        note_path.write_text(note_content, encoding="utf-8")

        logger.info(f"Updated note: {note_path}")
        return note_path

    def delete_note(self, file_path: str) -> bool:
        """
        Delete a note file.

        Args:
            file_path: Relative path from notes directory

        Returns:
            True if deleted, False if not found
        """
        note_path = self.notes_directory / file_path

        if not note_path.exists():
            logger.warning(f"Note not found for deletion: {note_path}")
            return False

        note_path.unlink()
        logger.info(f"Deleted note: {note_path}")
        return True

    def list_notes(self, subdirectory: Optional[str] = None) -> List[Path]:
        """
        List all note files.

        Args:
            subdirectory: Optional subdirectory to search within notes directory

        Returns:
            List of note file paths (relative to notes directory)
        """
        search_dir = (
            self.notes_directory / subdirectory if subdirectory else self.notes_directory
        )

        if not search_dir.exists():
            return []

        notes = list(search_dir.rglob("*.md"))
        # Convert to relative paths
        relative_notes = [
            note.relative_to(self.notes_directory) for note in notes
        ]
        logger.debug(f"Found {len(relative_notes)} notes")
        return relative_notes

    def get_note_metadata(self, file_path: str) -> NoteMetadata:
        """
        Get metadata for a note file.

        Args:
            file_path: Relative path from notes directory

        Returns:
            NoteMetadata instance
        """
        note_path = self.notes_directory / file_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        title, frontmatter, content = self.read_note(file_path)

        # Extract links from content
        links = self._extract_links(content)

        # Parse timestamps
        created_at_str = frontmatter.get("created_at", datetime.now().isoformat())
        updated_at_str = frontmatter.get("updated_at", datetime.now().isoformat())
        
        # Handle both string and datetime objects
        if isinstance(created_at_str, datetime):
            created_at = created_at_str
        elif isinstance(created_at_str, str):
            try:
                created_at = datetime.fromisoformat(created_at_str)
            except (ValueError, TypeError):
                created_at = datetime.now()
        else:
            created_at = datetime.now()
        
        if isinstance(updated_at_str, datetime):
            updated_at = updated_at_str
        elif isinstance(updated_at_str, str):
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
            except (ValueError, TypeError):
                updated_at = datetime.now()
        else:
            updated_at = datetime.now()

        # Get tags
        tags = frontmatter.get("tags", [])

        # Generate note ID from file path
        note_id = str(file_path).replace("\\", "/").replace(".md", "")

        return NoteMetadata(
            note_id=note_id,
            title=title,
            file_path=str(file_path),
            created_at=created_at,
            updated_at=updated_at,
            tags=tags if isinstance(tags, list) else [tags] if tags else [],
            links=links,
            frontmatter=frontmatter,
        )

    def _extract_links(self, content: str) -> List[str]:
        """
        Extract Obsidian-style links [[note-name]] from content.

        Args:
            content: Note content

        Returns:
            List of linked note names
        """
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, content)
        return list(set(matches))  # Return unique links

    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Parse YAML frontmatter from note content.

        Args:
            content: Note content with optional frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter_str, body = match.groups()
            try:
                frontmatter = yaml.safe_load(frontmatter_str) or {}
                return frontmatter, body
            except yaml.YAMLError as e:
                logger.warning(f"Error parsing frontmatter: {e}")
                return {}, content

        return {}, content

    def _build_note_content(self, frontmatter: Dict, content: str) -> str:
        """
        Build note content with frontmatter.

        Args:
            frontmatter: Frontmatter dictionary
            content: Note body content

        Returns:
            Complete note content with frontmatter
        """
        if not frontmatter:
            return content

        frontmatter_yaml = yaml.dump(
            frontmatter, allow_unicode=True, default_flow_style=False
        )
        return f"---\n{frontmatter_yaml}---\n\n{content}"

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters for Windows/Unix
        invalid_chars = r'<>:"/\|?*'
        sanitized = "".join(c if c not in invalid_chars else "_" for c in filename)
        return sanitized.strip()

    def _extract_title_from_path(self, file_path: str) -> str:
        """
        Extract title from file path.

        Args:
            file_path: File path

        Returns:
            Title extracted from path
        """
        path = Path(file_path)
        return path.stem.replace("_", " ").replace("-", " ").title()

