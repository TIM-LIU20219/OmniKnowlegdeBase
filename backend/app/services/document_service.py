"""Document service for orchestrating document processing pipeline."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from backend.app.models.metadata import DocumentMetadata, SourceType
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.document_processor import DocumentProcessor
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_service import VectorService
from backend.app.utils.file_hash import get_file_hash_and_metadata
from backend.app.utils.filesystem import BASE_DIR, DOCUMENTS_DIR, ensure_file_directory

logger = logging.getLogger(__name__)


class DuplicateDocumentError(Exception):
    """Exception raised when attempting to add a duplicate document."""

    def __init__(self, message: str, existing_doc: Optional[DocumentMetadata] = None):
        """
        Initialize duplicate document error.

        Args:
            message: Error message
            existing_doc: Existing document metadata if found
        """
        super().__init__(message)
        self.existing_doc = existing_doc


class DocumentService:
    """Service for processing and storing documents."""

    def __init__(
        self,
        vector_service: Optional[VectorService] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize document service.

        Args:
            vector_service: Optional VectorService instance
            chunking_service: Optional ChunkingService instance
            embedding_service: Optional EmbeddingService instance
        """
        self.processor = DocumentProcessor()
        self.vector_service = vector_service or VectorService()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()

        logger.info("Document service initialized")

    def _check_duplicate(self, file_hash: str) -> Optional[DocumentMetadata]:
        """
        Check if document with same hash already exists.

        Args:
            file_hash: SHA256 hash of file content

        Returns:
            Existing DocumentMetadata if found, None otherwise
        """
        try:
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)

            # Query by file_hash
            results = collection.get(
                where={"file_hash": file_hash}, include=["metadatas"]
            )

            if results["ids"]:
                # Get first chunk's metadata (all chunks have same doc_id)
                metadata_dict = results["metadatas"][0]
                return DocumentMetadata.from_chromadb_metadata(metadata_dict)

            return None
        except Exception as e:
            logger.warning(f"Error checking duplicate: {e}")
            return None

    def _should_copy_file(self, file_path: Path) -> bool:
        """
        Determine if file should be copied to documents folder.

        Strategy:
        - If file is in resources folder, keep reference only
        - If file is uploaded (temp location), copy to documents

        Args:
            file_path: Source file path

        Returns:
            True if file should be copied, False otherwise
        """
        try:
            # Resolve paths to absolute
            file_path_resolved = file_path.resolve()
            resources_dir = BASE_DIR / "resources"

            # Check if file is in resources folder
            try:
                file_path_resolved.relative_to(resources_dir.resolve())
                # File is in resources, don't copy
                logger.debug(f"File is in resources folder, keeping reference: {file_path}")
                return False
            except ValueError:
                # File is not in resources, copy it
                logger.debug(f"File is not in resources folder, will copy: {file_path}")
                return True
        except Exception as e:
            logger.warning(f"Error determining copy strategy: {e}, defaulting to copy")
            return True

    def process_and_store_markdown(
        self,
        content: str,
        file_path: Optional[str] = None,
        skip_duplicates: bool = True,
        import_batch: Optional[str] = None,
    ) -> DocumentMetadata:
        """
        Process markdown content and store in vector database.

        Args:
            content: Markdown content
            file_path: Optional file path
            skip_duplicates: If True, skip files that already exist
            import_batch: Optional batch identifier for tracking

        Returns:
            DocumentMetadata of the processed document

        Raises:
            DuplicateDocumentError: If duplicate found and skip_duplicates=True
        """
        try:
            # Process markdown
            text, metadata = self.processor.process_markdown(content, file_path)

            # If file_path is provided, calculate hash and check duplicates
            if file_path:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    file_info = get_file_hash_and_metadata(file_path_obj)
                    file_hash = file_info["file_hash"]

                    if skip_duplicates:
                        existing = self._check_duplicate(file_hash)
                        if existing:
                            logger.info(
                                f"Document already exists: {existing.title} "
                                f"(ID: {existing.doc_id}, Hash: {file_hash[:8]}...)"
                            )
                            raise DuplicateDocumentError(
                                f"Document with same content already exists: {existing.title}",
                                existing_doc=existing,
                            )

                    # Enhance metadata
                    metadata.file_hash = file_hash
                    metadata.file_size = file_info["file_size"]
                    metadata.file_mtime = file_info["file_mtime"]

                    # Determine storage strategy
                    should_copy = self._should_copy_file(file_path_obj)
                    if should_copy:
                        saved_path = self._save_document_file(file_path_obj, "md")
                        metadata.storage_path = str(saved_path)
                    else:
                        try:
                            metadata.original_path = str(file_path_obj.relative_to(BASE_DIR))
                            metadata.storage_path = metadata.original_path
                        except ValueError:
                            metadata.storage_path = str(file_path_obj)

            metadata.import_batch = import_batch

            # Process and store
            return self._process_and_store(text, metadata)

        except DuplicateDocumentError:
            raise
        except Exception as e:
            logger.error(f"Error processing markdown: {e}")
            raise

    def process_and_store_pdf(
        self,
        file_path: Path,
        skip_duplicates: bool = True,
        import_batch: Optional[str] = None,
    ) -> DocumentMetadata:
        """
        Process PDF file and store in vector database.

        Args:
            file_path: Path to PDF file
            skip_duplicates: If True, skip files that already exist
            import_batch: Optional batch identifier for tracking

        Returns:
            DocumentMetadata of the processed document

        Raises:
            DuplicateDocumentError: If duplicate found and skip_duplicates=True
        """
        try:
            # Calculate file hash and metadata
            file_info = get_file_hash_and_metadata(file_path)
            file_hash = file_info["file_hash"]

            # Check for duplicates
            if skip_duplicates:
                existing = self._check_duplicate(file_hash)
                if existing:
                    logger.info(
                        f"Document already exists: {existing.title} "
                        f"(ID: {existing.doc_id}, Hash: {file_hash[:8]}...)"
                    )
                    raise DuplicateDocumentError(
                        f"Document with same content already exists: {existing.title}",
                        existing_doc=existing,
                    )

            # Determine storage strategy
            should_copy = self._should_copy_file(file_path)
            original_path = None

            if should_copy:
                saved_path = self._save_document_file(file_path, "pdf")
                storage_path = str(saved_path)
            else:
                # Keep original path, store reference only
                saved_path = file_path
                try:
                    original_path = str(file_path.relative_to(BASE_DIR))
                except ValueError:
                    # If relative path calculation fails, use absolute path
                    original_path = str(file_path)
                storage_path = original_path

            # Process PDF
            text, metadata = self.processor.process_pdf(saved_path)

            # Enhance metadata
            metadata.file_hash = file_hash
            metadata.file_size = file_info["file_size"]
            metadata.file_mtime = file_info["file_mtime"]
            metadata.original_path = original_path
            metadata.storage_path = storage_path
            metadata.import_batch = import_batch

            # Process and store
            return self._process_and_store(text, metadata)

        except DuplicateDocumentError:
            raise
        except Exception as e:
            logger.error(f"Error processing PDF '{file_path}': {e}")
            raise

    def process_and_store_url(
        self, url: str, import_batch: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Process URL and store in vector database.

        Args:
            url: URL to fetch and process
            import_batch: Optional batch identifier for tracking

        Returns:
            DocumentMetadata of the processed document
        """
        try:
            # Process URL
            text, metadata = self.processor.process_url(url)

            # Add import batch if provided
            metadata.import_batch = import_batch

            # Process and store
            return self._process_and_store(text, metadata)

        except Exception as e:
            logger.error(f"Error processing URL '{url}': {e}")
            raise

    def _process_and_store(
        self, text: str, metadata: DocumentMetadata
    ) -> DocumentMetadata:
        """
        Process text and store chunks in vector database.

        Args:
            text: Processed text content
            metadata: Document metadata

        Returns:
            Updated DocumentMetadata with chunk information
        """
        try:
            # Chunk text
            chunks = self.chunking_service.chunk_text(text)
            total_chunks = len(chunks)

            if not chunks:
                logger.warning(f"No chunks generated for document: {metadata.title}")
                return metadata

            logger.info(
                f"Generated {total_chunks} chunks for document: {metadata.title}"
            )

            # Generate embeddings
            embeddings = self.embedding_service.embed_texts(chunks)

            # Prepare documents, IDs, and metadatas for ChromaDB
            document_ids = []
            document_texts = []
            document_metadatas = []

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create chunk ID
                chunk_id = f"{metadata.doc_id}_chunk_{i}"

                # Update metadata for this chunk
                chunk_metadata = metadata.model_copy()
                chunk_metadata.chunk_index = i
                chunk_metadata.chunk_total = total_chunks

                document_ids.append(chunk_id)
                document_texts.append(chunk)
                document_metadatas.append(chunk_metadata.to_chromadb_metadata())

            # Store in vector database
            collection_name = self.vector_service.collection_names["documents"]
            self.vector_service.add_documents(
                collection_name=collection_name,
                documents=document_texts,
                ids=document_ids,
                metadatas=document_metadatas,
                embeddings=embeddings,
            )

            logger.info(
                f"Stored {total_chunks} chunks for document: {metadata.title}"
            )

            # Update metadata with chunk information
            metadata.chunk_total = total_chunks
            return metadata

        except Exception as e:
            logger.error(f"Error processing and storing document: {e}")
            raise

    def _save_document_file(self, file_path: Path, extension: str) -> Path:
        """
        Save uploaded file to documents directory.

        Args:
            file_path: Source file path
            extension: File extension

        Returns:
            Path to saved file
        """
        # Generate unique filename
        filename = f"{uuid4().hex}.{extension}"
        saved_path = DOCUMENTS_DIR / filename

        # Ensure directory exists
        ensure_file_directory(saved_path)

        # Copy file
        import shutil

        shutil.copy2(file_path, saved_path)

        logger.info(f"Saved document file: {saved_path}")
        return saved_path

    def delete_document(self, doc_id: str):
        """
        Delete document and all its chunks from vector database.

        Args:
            doc_id: Document ID to delete
        """
        try:
            collection_name = self.vector_service.collection_names["documents"]

            # Query all chunks for this document
            collection = self.vector_service.get_or_create_collection(collection_name)
            results = collection.get(where={"doc_id": doc_id})

            if results["ids"]:
                # Delete all chunks
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document: {doc_id}")
            else:
                logger.warning(f"No chunks found for document: {doc_id}")

        except Exception as e:
            logger.error(f"Error deleting document '{doc_id}': {e}")
            raise

    def get_document_chunks(self, doc_id: str) -> List[Tuple[str, dict]]:
        """
        Get all chunks for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of (chunk_text, metadata) tuples
        """
        try:
            collection_name = self.vector_service.collection_names["documents"]
            collection = self.vector_service.get_or_create_collection(collection_name)

            # Query all chunks for this document
            results = collection.get(where={"doc_id": doc_id})

            chunks = []
            if results["ids"]:
                # Sort by chunk_index
                indices = [int(m["chunk_index"]) for m in results["metadatas"]]
                sorted_indices = sorted(range(len(indices)), key=lambda i: indices[i])

                for idx in sorted_indices:
                    chunk_text = results["documents"][idx]
                    metadata = results["metadatas"][idx]
                    chunks.append((chunk_text, metadata))

            return chunks

        except Exception as e:
            logger.error(f"Error getting chunks for document '{doc_id}': {e}")
            raise

