"""RAG service for retrieval-augmented generation."""

import logging
from typing import AsyncIterator, Iterator, List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.retriever import ChromaDBRetriever
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

# Default RAG prompt template
DEFAULT_RAG_PROMPT = """Use the following pieces of context to answer the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Answer:"""


class RAGService:
    """
    RAG service that combines retrieval and generation.
    
    This service performs semantic search to retrieve relevant documents,
    then uses an LLM to generate answers based on the retrieved context.
    """

    def __init__(
        self,
        vector_service: VectorService,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        collection_name: str = "documents",
        k: int = 4,
        score_threshold: Optional[float] = None,
        prompt_template: Optional[str] = None,
        max_context_length: int = 4000,
    ):
        """
        Initialize RAG service.

        Args:
            vector_service: VectorService instance
            embedding_service: EmbeddingService instance
            llm_service: LLMService instance
            collection_name: ChromaDB collection name to query
            k: Number of documents to retrieve
            score_threshold: Optional similarity score threshold
            prompt_template: Optional custom prompt template
            max_context_length: Maximum context length in characters
        """
        self.retriever = ChromaDBRetriever(
            vector_service=vector_service,
            embedding_service=embedding_service,
            collection_name=collection_name,
            k=k,
            score_threshold=score_threshold,
        )
        self.llm_service = llm_service
        self.prompt_template = prompt_template or DEFAULT_RAG_PROMPT
        self.max_context_length = max_context_length

        logger.info(
            f"Initialized RAG service: collection={collection_name}, k={k}, "
            f"max_context_length={max_context_length}"
        )

    def _format_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            documents: List of retrieved documents

        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents):
            # Include metadata information
            doc_info = f"[Document {i+1}]"
            if "title" in doc.metadata:
                doc_info += f" Title: {doc.metadata['title']}"
            if "doc_id" in doc.metadata:
                doc_info += f" (ID: {doc.metadata['doc_id']})"

            doc_text = f"{doc_info}\n{doc.page_content}"

            # Check if adding this document would exceed max length
            if current_length + len(doc_text) > self.max_context_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)

        return "\n\n".join(context_parts)

    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build prompt from template.

        Args:
            question: User question
            context: Retrieved context

        Returns:
            Formatted prompt
        """
        prompt = PromptTemplate.from_template(self.prompt_template)
        return prompt.format(context=context, question=question)

    def query(
        self, question: str, metadata_filter: Optional[dict] = None
    ) -> dict:
        """
        Query RAG system synchronously.

        Args:
            question: User question
            metadata_filter: Optional metadata filter for retrieval

        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Update retriever metadata filter if provided
            if metadata_filter:
                self.retriever.metadata_filter = metadata_filter

            # Retrieve relevant documents
            documents = self.retriever.get_relevant_documents(question)

            if not documents:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "metadata": {"retrieved_count": 0},
                }

            # Format context
            context = self._format_context(documents)

            # Build prompt
            prompt = self._build_prompt(question, context)

            # Generate answer
            answer = self.llm_service.invoke(prompt)

            # Extract source information
            sources = []
            for doc in documents:
                source_info = {
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "title": doc.metadata.get("title", "Unknown"),
                    "doc_id": doc.metadata.get("doc_id"),
                    "distance": doc.metadata.get("distance"),
                }
                sources.append(source_info)

            return {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "retrieved_count": len(documents),
                    "context_length": len(context),
                },
            }

        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)},
            }

    def stream_query(
        self, question: str, metadata_filter: Optional[dict] = None
    ) -> Iterator[str]:
        """
        Stream query response.

        Args:
            question: User question
            metadata_filter: Optional metadata filter for retrieval

        Yields:
            Text chunks as they are generated
        """
        try:
            # Update retriever metadata filter if provided
            if metadata_filter:
                self.retriever.metadata_filter = metadata_filter

            # Retrieve relevant documents
            documents = self.retriever.get_relevant_documents(question)

            if not documents:
                yield "I couldn't find any relevant information to answer your question."
                return

            # Format context
            context = self._format_context(documents)

            # Build prompt
            prompt = self._build_prompt(question, context)

            # Stream answer
            for chunk in self.llm_service.stream(prompt):
                yield chunk

        except Exception as e:
            logger.error(f"Error in RAG stream query: {e}")
            yield f"Error generating answer: {str(e)}"

    async def aquery(
        self, question: str, metadata_filter: Optional[dict] = None
    ) -> dict:
        """
        Query RAG system asynchronously.

        Args:
            question: User question
            metadata_filter: Optional metadata filter for retrieval

        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Update retriever metadata filter if provided
            if metadata_filter:
                self.retriever.metadata_filter = metadata_filter

            # Retrieve relevant documents
            documents = await self.retriever.aget_relevant_documents(question)

            if not documents:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "metadata": {"retrieved_count": 0},
                }

            # Format context
            context = self._format_context(documents)

            # Build prompt
            prompt = self._build_prompt(question, context)

            # Generate answer
            answer = await self.llm_service.ainvoke(prompt)

            # Extract source information
            sources = []
            for doc in documents:
                source_info = {
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "title": doc.metadata.get("title", "Unknown"),
                    "doc_id": doc.metadata.get("doc_id"),
                    "distance": doc.metadata.get("distance"),
                }
                sources.append(source_info)

            return {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "retrieved_count": len(documents),
                    "context_length": len(context),
                },
            }

        except Exception as e:
            logger.error(f"Error in RAG async query: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)},
            }

    async def astream_query(
        self, question: str, metadata_filter: Optional[dict] = None
    ) -> AsyncIterator[str]:
        """
        Stream query response asynchronously.

        Args:
            question: User question
            metadata_filter: Optional metadata filter for retrieval

        Yields:
            Text chunks as they are generated
        """
        try:
            # Update retriever metadata filter if provided
            if metadata_filter:
                self.retriever.metadata_filter = metadata_filter

            # Retrieve relevant documents
            documents = await self.retriever.aget_relevant_documents(question)

            if not documents:
                yield "I couldn't find any relevant information to answer your question."
                return

            # Format context
            context = self._format_context(documents)

            # Build prompt
            prompt = self._build_prompt(question, context)

            # Stream answer
            async for chunk in self.llm_service.astream(prompt):
                yield chunk

        except Exception as e:
            logger.error(f"Error in RAG async stream query: {e}")
            yield f"Error generating answer: {str(e)}"

