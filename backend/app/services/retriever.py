"""Retriever service for RAG - wraps VectorService for LangChain compatibility."""

import logging
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class ChromaDBRetriever(BaseRetriever):
    """
    LangChain-compatible retriever wrapper for ChromaDB VectorService.
    
    This retriever performs semantic search using ChromaDB and returns
    LangChain Document objects with metadata.
    """

    vector_service: VectorService = Field(exclude=True)
    embedding_service: EmbeddingService = Field(exclude=True)
    collection_name: str
    k: int = 4
    score_threshold: Optional[float] = None
    metadata_filter: Optional[dict] = None

    def __init__(
        self,
        vector_service: VectorService,
        embedding_service: EmbeddingService,
        collection_name: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[dict] = None,
        **kwargs,
    ):
        """
        Initialize ChromaDB retriever.

        Args:
            vector_service: VectorService instance for ChromaDB queries
            embedding_service: EmbeddingService for query embeddings
            collection_name: Name of ChromaDB collection to query
            k: Number of documents to retrieve (default: 4)
            score_threshold: Optional similarity score threshold (0-1)
            metadata_filter: Optional metadata filter dict for ChromaDB where clause
        """
        super().__init__(
            vector_service=vector_service,
            embedding_service=embedding_service,
            collection_name=collection_name,
            k=k,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter,
            **kwargs,
        )

        logger.info(
            f"Initialized ChromaDBRetriever: collection={collection_name}, k={k}"
        )

    def _get_relevant_documents(
        self, query: str
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query string

        Returns:
            List of LangChain Document objects
        """
        try:
            # Validate embedding dimension before querying
            # Temporarily disabled to let ChromaDB report actual error
            # self._validate_embedding_dimension()
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)

            # Query ChromaDB
            results = self.vector_service.query(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=self.k,
                where=self.metadata_filter,
            )

            # Convert ChromaDB results to LangChain Documents
            documents = []
            if results and "ids" in results and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents_list = results.get("documents", [[]])[0]
                metadatas_list = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i, (doc_id, doc_text, metadata) in enumerate(
                    zip(ids, documents_list, metadatas_list)
                ):
                    # Apply score threshold if specified
                    if self.score_threshold is not None:
                        # ChromaDB uses distance (lower is better), convert to similarity
                        # Cosine similarity ≈ 1 - distance (for normalized vectors)
                        similarity = 1.0 - distances[i] if distances else 1.0
                        if similarity < self.score_threshold:
                            continue

                    # Create LangChain Document
                    doc = Document(
                        page_content=doc_text,
                        metadata={
                            **metadata,
                            "chunk_id": doc_id,
                            "distance": distances[i] if distances else None,
                        },
                    )
                    documents.append(doc)

            logger.debug(
                f"Retrieved {len(documents)} documents for query: {query[:50]}..."
            )
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    def _validate_embedding_dimension(self):
        """
        Validate that the embedding service dimension matches the collection dimension.
        
        This validation is done by attempting a test query. If the query fails due to
        dimension mismatch, ChromaDB will raise an error with the expected dimension.
        
        Raises:
            ValueError: If dimensions don't match
        """
        # Get collection dimension (may return None if collection is empty or check fails)
        collection_dim = self.vector_service.get_collection_embedding_dimension(
            self.collection_name
        )
        
        # If collection is empty, skip validation
        if collection_dim is None:
            logger.debug("Collection is empty or dimension check failed, skipping validation")
            return
        
        # Get current embedding service dimension
        current_dim = self.embedding_service.get_embedding_dimension()
        
        if collection_dim != current_dim:
            error_msg = (
                f"Embedding dimension mismatch!\n"
                f"  Collection '{self.collection_name}' expects: {collection_dim} dimensions\n"
                f"  Current model '{self.embedding_service.model_name}' generates: {current_dim} dimensions\n\n"
                f"Solution:\n"
                f"  1. Set EMBEDDING_MODEL environment variable to match the model used for indexing\n"
                f"  2. Or re-index all documents with the current model\n"
                f"  3. Check your .env file for EMBEDDING_MODEL configuration"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log dimension match for debugging
        logger.debug(
            f"Embedding dimension validated: collection={collection_dim}D, "
            f"model={current_dim}D"
        )

    async def _aget_relevant_documents(
        self, query: str
    ) -> List[Document]:
        """
        Async version of _get_relevant_documents.

        Args:
            query: Query string

        Returns:
            List of LangChain Document objects
        """
        # For now, use sync version (ChromaDB query is sync)
        return self._get_relevant_documents(query)

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Public method to retrieve relevant documents (LangChain interface).

        Args:
            query: Query string

        Returns:
            List of LangChain Document objects
        """
        return self._get_relevant_documents(query)

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """
        Public async method to retrieve relevant documents (LangChain interface).

        Args:
            query: Query string

        Returns:
            List of LangChain Document objects
        """
        return await self._aget_relevant_documents(query)

    def retrieve_with_context(
        self, query: str, include_source_info: bool = True
    ) -> List[dict]:
        """
        Retrieve documents with enhanced context information.

        Args:
            query: Query string
            include_source_info: If True, include source file information

        Returns:
            List of dicts with keys:
            - text: chunk text
            - metadata: full DocumentMetadata
            - score: similarity score
            - source_info: (if include_source_info) dict with original_path,
              storage_path, file_size, import_batch, etc.
        """
        documents = self.get_relevant_documents(query)

        enhanced_results = []
        for doc in documents:
            enhanced = {
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": 1.0 - doc.metadata.get("distance", 0)
                if doc.metadata.get("distance") is not None
                else None,
            }

            if include_source_info:
                meta = doc.metadata
                enhanced["source_info"] = {
                    "original_path": meta.get("original_path"),
                    "storage_path": meta.get("storage_path"),
                    "file_size": meta.get("file_size"),
                    "file_mtime": meta.get("file_mtime"),
                    "import_batch": meta.get("import_batch"),
                    "file_hash": meta.get("file_hash"),
                }

            enhanced_results.append(enhanced)

        return enhanced_results

