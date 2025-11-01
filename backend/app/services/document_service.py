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
from backend.app.utils.filesystem import DOCUMENTS_DIR, ensure_file_directory

logger = logging.getLogger(__name__)


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

    def process_and_store_markdown(
        self, content: str, file_path: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Process markdown content and store in vector database.

        Args:
            content: Markdown content
            file_path: Optional file path

        Returns:
            DocumentMetadata of the processed document
        """
        try:
            # Process markdown
            text, metadata = self.processor.process_markdown(content, file_path)

            # Process and store
            return self._process_and_store(text, metadata)

        except Exception as e:
            logger.error(f"Error processing markdown: {e}")
            raise

    def process_and_store_pdf(self, file_path: Path) -> DocumentMetadata:
        """
        Process PDF file and store in vector database.

        Args:
            file_path: Path to PDF file

        Returns:
            DocumentMetadata of the processed document
        """
        try:
            # Copy file to documents directory if needed
            if not file_path.is_absolute() or str(DOCUMENTS_DIR) not in str(file_path):
                saved_path = self._save_document_file(file_path, "pdf")
            else:
                saved_path = file_path

            # Process PDF
            text, metadata = self.processor.process_pdf(saved_path)

            # Process and store
            return self._process_and_store(text, metadata)

        except Exception as e:
            logger.error(f"Error processing PDF '{file_path}': {e}")
            raise

    def process_and_store_url(self, url: str) -> DocumentMetadata:
        """
        Process URL and store in vector database.

        Args:
            url: URL to fetch and process

        Returns:
            DocumentMetadata of the processed document
        """
        try:
            # Process URL
            text, metadata = self.processor.process_url(url)

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

