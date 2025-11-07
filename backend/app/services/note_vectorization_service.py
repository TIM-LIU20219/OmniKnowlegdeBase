"""Service for vectorizing notes and managing note embeddings."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from backend.app.models.metadata import DocumentMetadata, DocType, NoteMetadata, SourceType
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.vector_service import VectorService
from backend.app.utils.filesystem import NOTES_DIR
from backend.app.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class NoteVectorizationService:
    """Service for vectorizing notes and managing note embeddings."""

    def __init__(
        self,
        note_file_service: Optional[NoteFileService] = None,
        document_service: Optional[DocumentService] = None,
        note_metadata_service: Optional[NoteMetadataService] = None,
        vector_service: Optional[VectorService] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize note vectorization service.

        Args:
            note_file_service: Optional NoteFileService instance
            document_service: Optional DocumentService instance
            note_metadata_service: Optional NoteMetadataService instance
            vector_service: Optional VectorService instance
            chunking_service: Optional ChunkingService instance
            embedding_service: Optional EmbeddingService instance
        """
        self.note_file_service = note_file_service or NoteFileService()
        self.document_service = document_service or DocumentService()
        self.note_metadata_service = note_metadata_service or NoteMetadataService()
        self.vector_service = vector_service or VectorService()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()

        logger.info("Note vectorization service initialized")

    def is_note_vectorized(self, file_path: str) -> bool:
        """
        Check if a note is already vectorized in ChromaDB.

        Args:
            file_path: Relative path from notes directory

        Returns:
            True if note is vectorized, False otherwise
        """
        try:
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)

            # Generate note_id from file_path (same logic as DocumentService)
            note_id = str(file_path).replace("\\", "/").replace(".md", "")

            # Query for documents with matching file_path and doc_type=note
            results = collection.get(
                where={
                    "file_path": str(file_path),
                    "doc_type": DocType.NOTE.value,
                },
                limit=1,
            )

            return len(results["ids"]) > 0
        except Exception as e:
            logger.warning(f"Error checking if note is vectorized: {e}")
            return False

    def vectorize_note(self, file_path: str, force: bool = False) -> DocumentMetadata:
        """
        Vectorize a single note.

        Args:
            file_path: Relative path from notes directory
            force: If True, re-vectorize even if already vectorized

        Returns:
            DocumentMetadata of the vectorized note

        Raises:
            FileNotFoundError: If note file doesn't exist
        """
        note_path = self.note_file_service.notes_directory / file_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        # Check if already vectorized
        if not force and self.is_note_vectorized(file_path):
            logger.info(f"Note '{file_path}' is already vectorized. Use --force to re-vectorize.")
            # Get existing metadata from ChromaDB
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)
            results = collection.get(
                where={
                    "file_path": str(file_path),
                    "doc_type": DocType.NOTE.value,
                },
                limit=1,
            )
            if results["ids"]:
                metadata_dict = results["metadatas"][0]
                return DocumentMetadata.from_chromadb_metadata(metadata_dict)

        # Read note content
        title, frontmatter, content = self.note_file_service.read_note(file_path)

        # Delete existing vectors if force re-vectorizing
        if force:
            self._delete_note_vectors(file_path)

        # Process and store using DocumentService
        # This will handle:
        # 1. Extracting structured info (tags, links, frontmatter) -> SQLite
        # 2. Cleaning text for embedding
        # 3. Chunking and vectorizing -> ChromaDB
        # Pass absolute path so DocumentService can check file existence and calculate hash
        # DocumentService will detect it's a note based on path and doc_type
        metadata = self.document_service.process_and_store_markdown(
            content=content,
            file_path=str(note_path),
            skip_duplicates=False,  # Allow re-processing (we check duplicates ourselves)
        )

        logger.info(f"Vectorized note: {file_path} (doc_id: {metadata.doc_id})")
        return metadata

    def vectorize_all_notes(
        self, force: bool = False, incremental: bool = True
    ) -> Tuple[int, int]:
        """
        Vectorize all notes in the notes directory.

        Args:
            force: If True, re-vectorize all notes even if already vectorized
            incremental: If True, only vectorize notes that aren't already vectorized

        Returns:
            Tuple of (vectorized_count, skipped_count)
        """
        # Get all note files
        note_files = self.note_file_service.list_notes()
        total_notes = len(note_files)

        if total_notes == 0:
            logger.info("No notes found to vectorize")
            return (0, 0)

        logger.info(f"Found {total_notes} notes to process")

        vectorized_count = 0
        skipped_count = 0
        error_count = 0

        for note_file in note_files:
            file_path_str = str(note_file).replace("\\", "/")

            try:
                # Check if should skip
                if incremental and not force:
                    if self.is_note_vectorized(file_path_str):
                        logger.debug(f"Skipping already vectorized note: {file_path_str}")
                        skipped_count += 1
                        continue

                # Vectorize note
                self.vectorize_note(file_path_str, force=force)
                vectorized_count += 1
                logger.info(f"Vectorized {vectorized_count}/{total_notes}: {file_path_str}")

            except Exception as e:
                error_count += 1
                logger.error(f"Error vectorizing note '{file_path_str}': {e}")

        logger.info(
            f"Vectorization complete: {vectorized_count} vectorized, "
            f"{skipped_count} skipped, {error_count} errors"
        )

        return (vectorized_count, skipped_count)

    def update_note_metadata(self, file_path: str) -> NoteMetadata:
        """
        Update note metadata in SQLite without re-vectorizing.
        
        This is useful for updating tags and links when the note content changes
        or when fixing metadata format (e.g., normalizing tags to Obsidian style).

        Args:
            file_path: Relative path from notes directory

        Returns:
            Updated NoteMetadata
        """
        note_path = self.note_file_service.notes_directory / file_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        # Read note content
        title, frontmatter, content = self.note_file_service.read_note(file_path)

        # Process markdown to get metadata (but don't store in ChromaDB)
        text, metadata = self.document_service.processor.process_markdown(
            content, str(note_path)
        )

        # Check if this is a note
        if not self.document_service._is_note_path(str(note_path)):
            raise ValueError(f"File '{file_path}' is not in notes directory")

        # Extract structured information using DocumentService logic
        self.document_service._process_note_metadata(metadata, content)

        # Get updated metadata from SQLite
        note_id = str(file_path).replace("\\", "/").replace(".md", "")
        updated_metadata = self.note_metadata_service.get_note_metadata(note_id)

        if not updated_metadata:
            raise ValueError(f"Failed to update metadata for note: {file_path}")

        logger.info(f"Updated note metadata: {file_path}")
        return updated_metadata

    def update_all_notes_metadata(self) -> Tuple[int, int]:
        """
        Update metadata for all notes in SQLite without re-vectorizing.

        Returns:
            Tuple of (updated_count, error_count)
        """
        # Get all note files
        note_files = self.note_file_service.list_notes()
        total_notes = len(note_files)

        if total_notes == 0:
            logger.info("No notes found to update")
            return (0, 0)

        logger.info(f"Found {total_notes} notes to update metadata")

        updated_count = 0
        error_count = 0

        for note_file in note_files:
            file_path_str = str(note_file).replace("\\", "/")

            try:
                self.update_note_metadata(file_path_str)
                updated_count += 1
                logger.info(f"Updated {updated_count}/{total_notes}: {file_path_str}")

            except Exception as e:
                error_count += 1
                logger.error(f"Error updating metadata for note '{file_path_str}': {e}")

        logger.info(
            f"Metadata update complete: {updated_count} updated, {error_count} errors"
        )

        return (updated_count, error_count)

    def _delete_note_vectors(self, file_path: str):
        """
        Delete all vectors for a note from ChromaDB.

        Args:
            file_path: Relative path from notes directory
        """
        try:
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)

            # Find all chunks for this note
            results = collection.get(
                where={
                    "file_path": str(file_path),
                    "doc_type": DocType.NOTE.value,
                },
            )

            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} vectors for note: {file_path}")
        except Exception as e:
            logger.warning(f"Error deleting note vectors: {e}")

    def search_notes(
        self, query: Optional[str] = None, limit: int = 10, tag: Optional[str] = None
    ) -> List[dict]:
        """
        Search notes by semantic similarity or filter by tag.

        Args:
            query: Optional search query (if None, only tag filtering is performed)
            limit: Maximum number of results
            tag: Optional tag to filter by

        Returns:
            List of note search results with metadata
        """
        try:
            # If only tag is provided (no query), get notes from SQLite
            if not query and tag:
                return self._search_notes_by_tag(tag, limit)

            # If query is provided, search in ChromaDB
            if not query:
                raise ValueError("At least one of 'query' or 'tag' must be provided")

            collection_name = self.vector_service.collection_names["documents"]
            
            # Build where clause
            where_clause = {"doc_type": DocType.NOTE.value}

            # Query ChromaDB
            results = self.vector_service.query(
                collection_name=collection_name,
                query_texts=[query],
                n_results=limit * 2,  # Get more results to filter by tag if needed
                where=where_clause,
            )

            # Process results
            note_results = []
            if results["ids"] and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

                for i, (doc_id, doc_text, metadata_dict, distance) in enumerate(
                    zip(ids, documents, metadatas, distances)
                ):
                    # Filter by tag if specified
                    if tag:
                        # Normalize tag to Obsidian style (#tag)
                        normalized_tag = tag if tag.startswith("#") else f"#{tag}"
                        
                        note_tags = metadata_dict.get("tags", [])
                        if isinstance(note_tags, str):
                            # Parse JSON string if needed
                            import json
                            try:
                                note_tags = json.loads(note_tags)
                            except:
                                note_tags = []
                        
                        # Normalize note tags to Obsidian style for comparison
                        normalized_note_tags = [
                            t if t.startswith("#") else f"#{t}" for t in note_tags
                        ]
                        
                        if normalized_tag not in normalized_note_tags:
                            continue

                    # Get note metadata from SQLite if available
                    file_path = metadata_dict.get("file_path", "")
                    note_metadata = None
                    if file_path:
                        try:
                            note_id = str(file_path).replace("\\", "/").replace(".md", "")
                            note_metadata = self.note_metadata_service.get_note_metadata(note_id)
                        except:
                            pass

                    note_results.append(
                        {
                            "doc_id": doc_id,
                            "file_path": file_path,
                            "title": metadata_dict.get("title", ""),
                            "content": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                            "similarity": 1.0 - distance if distance else 0.0,
                            "chunk_index": metadata_dict.get("chunk_index", 0),
                            "tags": note_metadata.tags if note_metadata else metadata_dict.get("tags", []),
                            "links": note_metadata.links if note_metadata else [],
                        }
                    )

                    if len(note_results) >= limit:
                        break

            return note_results

        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            raise

    def _search_notes_by_tag(self, tag: str, limit: int) -> List[dict]:
        """
        Search notes by tag from SQLite.
        
        Normalizes tag to Obsidian style with # prefix if not present.

        Args:
            tag: Tag to search for (with or without # prefix)
            limit: Maximum number of results

        Returns:
            List of note search results with metadata
        """
        try:
            # Normalize tag to Obsidian style (#tag)
            normalized_tag = tag if tag.startswith("#") else f"#{tag}"
            
            # Get notes by tag from SQLite
            notes = self.note_metadata_service.get_notes_by_tag(normalized_tag)
            
            if not notes:
                return []

            # Limit results
            notes = notes[:limit]

            # Build results with content preview from ChromaDB if available
            note_results = []
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)

            for note in notes:
                # Try to get content preview from ChromaDB
                content_preview = ""
                try:
                    results = collection.get(
                        where={
                            "file_path": note.file_path,
                            "doc_type": DocType.NOTE.value,
                        },
                        limit=1,
                    )
                    if results.get("documents") and len(results["documents"]) > 0:
                        doc_text = results["documents"][0]
                        content_preview = doc_text[:200] + "..." if len(doc_text) > 200 else doc_text
                except Exception:
                    pass

                note_results.append(
                    {
                        "note_id": note.note_id,
                        "file_path": note.file_path,
                        "title": note.title,
                        "content": content_preview,
                        "similarity": None,  # No similarity score for tag-only search
                        "tags": note.tags,
                        "links": note.links,
                    }
                )

            return note_results

        except Exception as e:
            logger.error(f"Error searching notes by tag: {e}")
            raise

