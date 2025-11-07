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

