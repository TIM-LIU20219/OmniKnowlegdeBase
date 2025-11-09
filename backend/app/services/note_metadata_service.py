"""Service for managing note metadata - now uses ChromaDB instead of SQLite."""

import logging
from pathlib import Path
from typing import List, Optional

from backend.app.models.metadata import DocumentMetadata, NoteMetadata
from backend.app.services.chromadb_metadata_service import ChromaDBMetadataService

logger = logging.getLogger(__name__)


class NoteMetadataService:
    """
    Service for managing note metadata.
    
    Now uses ChromaDBMetadataService as backend (unified to ChromaDB).
    Maintains backward compatibility with existing code.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize note metadata service.

        Args:
            db_path: Optional path to SQLite database (deprecated, kept for compatibility).
                    Now uses ChromaDB instead.
        """
        # Use ChromaDBMetadataService as backend
        self.chromadb_service = ChromaDBMetadataService()
        logger.info("Initialized NoteMetadataService (using ChromaDB backend)")

    @property
    def db_path(self) -> Path:
        """Return db_path for backward compatibility (deprecated)."""
        from backend.app.utils.filesystem import BASE_DIR
        return BASE_DIR / "backend" / "app" / "db" / "notes.db"

    def create_note_metadata(self, note_metadata: NoteMetadata) -> NoteMetadata:
        """
        Create or update note metadata.
        
        Note: Metadata is now stored in ChromaDB during vectorization.
        This method is kept for backward compatibility but is a no-op.
        The actual storage happens in DocumentService when processing notes.

        Args:
            note_metadata: NoteMetadata instance

        Returns:
            NoteMetadata instance (unchanged)
        """
        # Metadata is stored in ChromaDB during vectorization
        # This method is kept for backward compatibility
        logger.debug(f"Note metadata will be stored in ChromaDB during vectorization: {note_metadata.note_id}")
        return note_metadata

    def get_note_metadata(self, note_id: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by note_id.

        Args:
            note_id: Note identifier

        Returns:
            NoteMetadata instance or None if not found
        """
        return self.chromadb_service.get_note_metadata(note_id)

    def get_note_metadata_by_path(self, file_path: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by file path.

        Args:
            file_path: File path relative to notes directory

        Returns:
            NoteMetadata instance or None if not found
        """
        return self.chromadb_service.get_note_metadata_by_path(file_path)

    def get_notes_by_tag(self, tag: str) -> List[NoteMetadata]:
        """
        Get all notes with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of NoteMetadata instances
        """
        return self.chromadb_service.get_notes_by_tag(tag)

    def get_linked_notes(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes linked from a given note.

        Args:
            note_id: Source note identifier

        Returns:
            List of linked NoteMetadata instances
        """
        return self.chromadb_service.get_linked_notes(note_id)

    def get_backlinks(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes that link to a given note (backlinks).

        Args:
            note_id: Target note identifier

        Returns:
            List of NoteMetadata instances that link to this note
        """
        return self.chromadb_service.get_backlinks(note_id)

    def delete_note_metadata(self, note_id: str) -> bool:
        """
        Delete note metadata.
        
        Note: This deletes from ChromaDB. The actual deletion should be done
        through VectorService to remove all chunks.

        Args:
            note_id: Note identifier

        Returns:
            True if deleted, False if not found
        """
        # Note: Actual deletion should be done through VectorService
        # This method is kept for backward compatibility
        logger.warning("delete_note_metadata is deprecated. Use VectorService.delete_document instead.")
        return False

    def list_all_notes(self) -> List[NoteMetadata]:
        """
        List all notes.

        Returns:
            List of NoteMetadata instances
        """
        try:
            collection = self.chromadb_service.vector_service.get_or_create_collection(
                self.chromadb_service.collection_name
            )
            
            results = collection.get(
                where={"doc_type": "note"},
                include=["metadatas"]
            )
            
            notes = []
            seen_note_ids = set()
            
            for metadata_dict in results.get("metadatas", []):
                doc_id = metadata_dict.get("doc_id")
                if doc_id and doc_id not in seen_note_ids:
                    seen_note_ids.add(doc_id)
                    # Get first chunk for each note
                    note_chunks = collection.get(
                        where={"doc_id": doc_id},
                        limit=1,
                        include=["metadatas"]
                    )
                    if note_chunks["metadatas"]:
                        doc_metadata = DocumentMetadata.from_chromadb_metadata(
                            note_chunks["metadatas"][0]
                        )
                        note_metadata = self.chromadb_service._document_to_note_metadata(doc_metadata)
                        notes.append(note_metadata)
            
            return notes
        except Exception as e:
            logger.error(f"Error listing all notes: {e}")
            return []


