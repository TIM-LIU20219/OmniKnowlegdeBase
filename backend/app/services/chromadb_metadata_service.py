"""Service for querying note and document metadata from ChromaDB."""

import logging
from datetime import datetime
from typing import List, Optional

from backend.app.models.metadata import DocumentMetadata, DocType, NoteMetadata, SourceType
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class ChromaDBMetadataService:
    """
    Unified metadata service using ChromaDB.
    
    Replaces SQLite-based NoteMetadataService with ChromaDB-only solution.
    Supports all material types: PDF, URL, picture, note, etc.
    """
    
    def __init__(self, vector_service: Optional[VectorService] = None):
        """
        Initialize ChromaDB metadata service.
        
        Args:
            vector_service: Optional VectorService instance
        """
        self.vector_service = vector_service or VectorService()
        self.collection_name = self.vector_service.collection_names["documents"]
        logger.info("ChromaDB metadata service initialized")
    
    def get_notes_by_tag(self, tag: str) -> List[NoteMetadata]:
        """
        Get all notes with a specific tag.
        
        Uses ChromaDB document search to find notes containing the tag.
        
        Args:
            tag: Tag name (with or without # prefix)
            
        Returns:
            List of NoteMetadata instances
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            # Normalize tag to Obsidian style (#tag)
            normalized_tag = tag if tag.startswith("#") else f"#{tag}"
            
            # Method 1: Use document search (searches in content)
            results = collection.query(
                query_texts=[""],  # Empty query, just filtering
                n_results=1000,  # Get enough results
                where={
                    "doc_type": DocType.NOTE.value,
                },
                where_document={"$contains": normalized_tag}
            )
            
            # Method 2: Filter by metadata tags (application layer)
            # This is more precise but requires getting all notes first
            all_notes = collection.get(
                where={"doc_type": DocType.NOTE.value},
                include=["metadatas"]
            )
            
            note_metadata_list = []
            seen_note_ids = set()
            
            # Process results from document search
            if results.get("ids") and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata_dict = results["metadatas"][0][i]
                    note_id = metadata_dict.get("doc_id", doc_id)
                    
                    if note_id in seen_note_ids:
                        continue
                    seen_note_ids.add(note_id)
                    
                    # Get all chunks for this note to build full metadata
                    note_chunks = collection.get(
                        where={
                            "doc_id": note_id,
                            "doc_type": DocType.NOTE.value
                        },
                        include=["metadatas"],
                        limit=1
                    )
                    
                    if note_chunks["ids"]:
                        # Use first chunk's metadata
                        full_metadata = DocumentMetadata.from_chromadb_metadata(
                            note_chunks["metadatas"][0]
                        )
                        note_metadata = self._document_to_note_metadata(full_metadata)
                        note_metadata_list.append(note_metadata)
            
            # Also check metadata tags (more precise)
            for metadata_dict in all_notes.get("metadatas", []):
                tags_str = metadata_dict.get("tags", "")
                if tags_str:
                    tags_list = tags_str.split(",") if isinstance(tags_str, str) else tags_str
                    normalized_tags = [
                        t.strip() if t.strip().startswith("#") else f"#{t.strip()}"
                        for t in tags_list
                    ]
                    
                    if normalized_tag in normalized_tags:
                        note_id = metadata_dict.get("doc_id")
                        if note_id and note_id not in seen_note_ids:
                            seen_note_ids.add(note_id)
                            full_metadata = DocumentMetadata.from_chromadb_metadata(metadata_dict)
                            note_metadata = self._document_to_note_metadata(full_metadata)
                            note_metadata_list.append(note_metadata)
            
            logger.debug(f"Found {len(note_metadata_list)} notes with tag '{tag}'")
            return note_metadata_list
            
        except Exception as e:
            logger.error(f"Error getting notes by tag: {e}")
            return []
    
    def get_linked_notes(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes linked from a given note.
        
        Args:
            note_id: Source note identifier
            
        Returns:
            List of linked NoteMetadata instances
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            # Get source note
            source_results = collection.get(
                where={
                    "doc_id": note_id,
                    "doc_type": DocType.NOTE.value
                },
                limit=1,
                include=["metadatas"]
            )
            
            if not source_results["ids"]:
                logger.debug(f"Note '{note_id}' not found")
                return []
            
            # Get links from metadata
            source_metadata = DocumentMetadata.from_chromadb_metadata(
                source_results["metadatas"][0]
            )
            links = source_metadata.links
            
            if not links:
                return []
            
            # Find linked notes
            linked_notes = []
            for link_name in links:
                # Try to find note by various methods
                # Method 1: By doc_id
                results = collection.get(
                    where={"doc_id": link_name},
                    limit=1,
                    include=["metadatas"]
                )
                
                # Method 2: By file_path
                if not results["ids"]:
                    # ChromaDB doesn't support $contains in where clause directly
                    # So we need to get all notes and filter
                    all_notes = collection.get(
                        where={"doc_type": DocType.NOTE.value},
                        include=["metadatas"]
                    )
                    for metadata_dict in all_notes.get("metadatas", []):
                        file_path = metadata_dict.get("file_path", "")
                        if link_name in file_path or file_path.replace(".md", "") == link_name:
                            results = collection.get(
                                where={"doc_id": metadata_dict.get("doc_id")},
                                limit=1,
                                include=["metadatas"]
                            )
                            break
                
                # Method 3: By title (using document search)
                if not results["ids"]:
                    search_results = collection.query(
                        query_texts=[link_name],
                        n_results=5,
                        where={"doc_type": DocType.NOTE.value}
                    )
                    if search_results.get("ids") and len(search_results["ids"]) > 0:
                        # Get first result's metadata
                        first_id = search_results["ids"][0][0]
                        results = collection.get(
                            where={"doc_id": first_id},
                            limit=1,
                            include=["metadatas"]
                        )
                
                if results["ids"]:
                    linked_metadata = DocumentMetadata.from_chromadb_metadata(
                        results["metadatas"][0]
                    )
                    linked_note = self._document_to_note_metadata(linked_metadata)
                    linked_notes.append(linked_note)
            
            logger.debug(f"Found {len(linked_notes)} linked notes for '{note_id}'")
            return linked_notes
            
        except Exception as e:
            logger.error(f"Error getting linked notes: {e}")
            return []
    
    def get_backlinks(self, note_id: str) -> List[NoteMetadata]:
        """
        Get all notes that link to a given note (backlinks).
        
        Uses document search to find notes containing links to this note.
        
        Args:
            note_id: Target note identifier
            
        Returns:
            List of NoteMetadata instances that link to this note
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            # Get target note to find its title/file_path for searching
            target_results = collection.get(
                where={"doc_id": note_id},
                limit=1,
                include=["metadatas"]
            )
            
            if not target_results["ids"]:
                return []
            
            target_metadata = DocumentMetadata.from_chromadb_metadata(
                target_results["metadatas"][0]
            )
            
            # Search for notes that link to this note
            # Method 1: Search in document content for [[link]] patterns
            search_terms = [
                f"[[{note_id}]]",
                f"[[{target_metadata.title}]]",
            ]
            
            # Also try file_path without extension
            if target_metadata.file_path:
                file_stem = target_metadata.file_path.replace("\\", "/").replace(".md", "")
                search_terms.append(f"[[{file_stem}]]")
            
            backlinks = []
            seen_note_ids = set()
            
            for search_term in search_terms:
                results = collection.query(
                    query_texts=[""],
                    n_results=100,
                    where={"doc_type": DocType.NOTE.value},
                    where_document={"$contains": search_term}
                )
                
                if results.get("ids") and len(results["ids"]) > 0:
                    for doc_id in results["ids"][0]:
                        # Get full metadata for this note
                        note_results = collection.get(
                            where={"doc_id": doc_id},
                            limit=1,
                            include=["metadatas"]
                        )
                        
                        if note_results["ids"]:
                            note_id_from_result = note_results["metadatas"][0].get("doc_id", doc_id)
                            if note_id_from_result not in seen_note_ids and note_id_from_result != note_id:
                                seen_note_ids.add(note_id_from_result)
                                note_metadata = DocumentMetadata.from_chromadb_metadata(
                                    note_results["metadatas"][0]
                                )
                                backlink_note = self._document_to_note_metadata(note_metadata)
                                backlinks.append(backlink_note)
            
            # Method 2: Check links metadata field
            all_notes = collection.get(
                where={"doc_type": DocType.NOTE.value},
                include=["metadatas"]
            )
            
            for metadata_dict in all_notes.get("metadatas", []):
                links_str = metadata_dict.get("links", "")
                if links_str:
                    links_list = links_str.split(",") if isinstance(links_str, str) else links_str
                    if note_id in links_list or target_metadata.title in links_list:
                        note_id_from_meta = metadata_dict.get("doc_id")
                        if note_id_from_meta and note_id_from_meta not in seen_note_ids:
                            seen_note_ids.add(note_id_from_meta)
                            note_metadata = DocumentMetadata.from_chromadb_metadata(metadata_dict)
                            backlink_note = self._document_to_note_metadata(note_metadata)
                            backlinks.append(backlink_note)
            
            logger.debug(f"Found {len(backlinks)} backlinks for '{note_id}'")
            return backlinks
            
        except Exception as e:
            logger.error(f"Error getting backlinks: {e}")
            return []
    
    def get_materials_by_type(self, source_type: SourceType) -> List[DocumentMetadata]:
        """
        Get all materials of a specific type (PDF, URL, picture, etc.).
        
        Args:
            source_type: Material type to filter by
            
        Returns:
            List of DocumentMetadata instances
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            results = collection.get(
                where={"source": source_type.value},
                include=["metadatas"]
            )
            
            materials = []
            seen_doc_ids = set()
            
            for metadata_dict in results.get("metadatas", []):
                doc_id = metadata_dict.get("doc_id")
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    # Get first chunk for each document
                    doc_chunks = collection.get(
                        where={"doc_id": doc_id},
                        limit=1,
                        include=["metadatas"]
                    )
                    if doc_chunks["metadatas"]:
                        material = DocumentMetadata.from_chromadb_metadata(
                            doc_chunks["metadatas"][0]
                        )
                        materials.append(material)
            
            logger.debug(f"Found {len(materials)} materials of type '{source_type.value}'")
            return materials
            
        except Exception as e:
            logger.error(f"Error getting materials by type: {e}")
            return []
    
    def get_materials_by_tag(self, tag: str) -> List[DocumentMetadata]:
        """
        Get all materials (not just notes) with a specific tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of DocumentMetadata instances
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            # Get all materials with this tag in metadata
            all_materials = collection.get(
                include=["metadatas"]
            )
            
            normalized_tag = tag if tag.startswith("#") else f"#{tag}"
            materials = []
            seen_doc_ids = set()
            
            for metadata_dict in all_materials.get("metadatas", []):
                tags_str = metadata_dict.get("tags", "")
                if tags_str:
                    tags_list = tags_str.split(",") if isinstance(tags_str, str) else tags_str
                    normalized_tags = [
                        t.strip() if t.strip().startswith("#") else f"#{t.strip()}"
                        for t in tags_list
                    ]
                    
                    if normalized_tag in normalized_tags:
                        doc_id = metadata_dict.get("doc_id")
                        if doc_id and doc_id not in seen_doc_ids:
                            seen_doc_ids.add(doc_id)
                            material = DocumentMetadata.from_chromadb_metadata(metadata_dict)
                            materials.append(material)
            
            logger.debug(f"Found {len(materials)} materials with tag '{tag}'")
            return materials
            
        except Exception as e:
            logger.error(f"Error getting materials by tag: {e}")
            return []
    
    def get_note_metadata(self, note_id: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by note_id.
        
        Args:
            note_id: Note identifier
            
        Returns:
            NoteMetadata instance or None if not found
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            results = collection.get(
                where={
                    "doc_id": note_id,
                    "doc_type": DocType.NOTE.value
                },
                limit=1,
                include=["metadatas"]
            )
            
            if not results["ids"]:
                return None
            
            doc_metadata = DocumentMetadata.from_chromadb_metadata(results["metadatas"][0])
            return self._document_to_note_metadata(doc_metadata)
            
        except Exception as e:
            logger.error(f"Error getting note metadata: {e}")
            return None
    
    def get_note_metadata_by_path(self, file_path: str) -> Optional[NoteMetadata]:
        """
        Get note metadata by file path.
        
        Args:
            file_path: File path relative to notes directory
            
        Returns:
            NoteMetadata instance or None if not found
        """
        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)
            
            # Get all notes and filter by file_path
            all_notes = collection.get(
                where={"doc_type": DocType.NOTE.value},
                include=["metadatas"]
            )
            
            for metadata_dict in all_notes.get("metadatas", []):
                if metadata_dict.get("file_path") == file_path:
                    doc_metadata = DocumentMetadata.from_chromadb_metadata(metadata_dict)
                    return self._document_to_note_metadata(doc_metadata)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting note metadata by path: {e}")
            return None
    
    def _document_to_note_metadata(self, doc_metadata: DocumentMetadata) -> NoteMetadata:
        """
        Convert DocumentMetadata to NoteMetadata.
        
        Args:
            doc_metadata: DocumentMetadata instance
            
        Returns:
            NoteMetadata instance
        """
        # Parse file_path to get note_id
        note_id = (
            doc_metadata.file_path.replace("\\", "/").replace(".md", "")
            if doc_metadata.file_path
            else doc_metadata.doc_id
        )
        
        return NoteMetadata(
            note_id=note_id,
            title=doc_metadata.title,
            file_path=doc_metadata.file_path or "",
            tags=doc_metadata.tags,
            links=doc_metadata.links,
            created_at=datetime.fromisoformat(doc_metadata.created_at),
            updated_at=(
                datetime.fromisoformat(doc_metadata.updated_at)
                if doc_metadata.updated_at
                else datetime.now()
            ),
            frontmatter={},  # Could be extracted from metadata if stored
        )

