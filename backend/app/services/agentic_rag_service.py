"""Agentic RAG service that uses LLM tool calling for intelligent retrieval and generation."""

import logging
from typing import AsyncIterator, Dict, Iterator, List, Optional

from backend.app.services.agent_executor import AgentExecutor
from backend.app.services.agent_tools import AgentTools
from backend.app.services.agentic_search_service import AgenticSearchService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class AgenticRAGService:
    """
    Agentic RAG service that combines agentic search with generation.
    
    This service uses LLM tool calling to intelligently retrieve information
    from both structured notes (SQLite) and document chunks (ChromaDB),
    then generates answers based on the retrieved context.
    """

    def __init__(
        self,
        vector_service: Optional[VectorService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        llm_service: Optional[LLMService] = None,
        note_metadata_service: Optional[NoteMetadataService] = None,
        note_file_service: Optional[NoteFileService] = None,
        collection_name: str = "documents",
        max_iterations: int = 5,
        default_strategy: Optional[str] = None,
    ):
        """
        Initialize Agentic RAG service.

        Args:
            vector_service: Optional VectorService instance
            embedding_service: Optional EmbeddingService instance
            llm_service: Optional LLMService instance
            note_metadata_service: Optional NoteMetadataService instance
            note_file_service: Optional NoteFileService instance
            collection_name: ChromaDB collection name for document search
            max_iterations: Maximum number of tool calling iterations
            default_strategy: Default search strategy ("note-first", "hybrid", etc.)
        """
        self.vector_service = vector_service or VectorService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_service = llm_service or LLMService()
        self.note_metadata_service = note_metadata_service or NoteMetadataService()
        self.note_file_service = note_file_service or NoteFileService()
        self.collection_name = collection_name
        self.max_iterations = max_iterations
        self.default_strategy = default_strategy or "hybrid"

        # Initialize tools
        self.tools = AgentTools(
            note_metadata_service=self.note_metadata_service,
            note_file_service=self.note_file_service,
            vector_service=self.vector_service,
            embedding_service=self.embedding_service,
            collection_name=collection_name,
        )

        # Initialize agentic search service
        self.agentic_search_service = AgenticSearchService(
            tools=self.tools,
            default_strategy=self.default_strategy,
        )

        # Initialize agent executor
        self.executor = AgentExecutor(
            llm_service=self.llm_service,
            agentic_search_service=self.agentic_search_service,
            max_iterations=max_iterations,
        )

        logger.info(
            f"Initialized AgenticRAGService: collection={collection_name}, "
            f"max_iterations={max_iterations}, strategy={self.default_strategy}"
        )

    def _extract_sources(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Extract source information from tool calls.

        Args:
            tool_calls: List of tool call dictionaries

        Returns:
            List of source dictionaries
        """
        sources = []
        seen_ids = set()

        for tool_call in tool_calls:
            result = tool_call.get("result")
            if result is None:
                continue

            tool_name = tool_call.get("tool_name", "")

            # Extract note sources from list results
            if tool_name in [
                "search_notes_by_title",
                "get_notes_by_tag",
                "get_linked_notes",
                "get_backlinks",
            ]:
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            note_id = item.get("note_id")
                            if note_id and note_id not in seen_ids:
                                seen_ids.add(note_id)
                                sources.append(
                                    {
                                        "type": "note",
                                        "note_id": note_id,
                                        "title": item.get("title", "Unknown"),
                                        "file_path": item.get("file_path"),
                                        "tags": item.get("tags", []),
                                        "similarity": item.get("similarity"),
                                    }
                                )

            # Extract note source from single dict result
            elif tool_name == "get_note_metadata":
                if isinstance(result, dict) and result.get("note_id"):
                    note_id = result["note_id"]
                    if note_id not in seen_ids:
                        seen_ids.add(note_id)
                        sources.append(
                            {
                                "type": "note",
                                "note_id": note_id,
                                "title": result.get("title", "Unknown"),
                                "file_path": result.get("file_path"),
                                "tags": result.get("tags", []),
                            }
                        )

            # Note: read_note_content returns a string, not source info
            # Source info should come from previous tool calls

            # Extract document chunk sources
            elif tool_name == "search_pdf_chunks":
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            doc_id = item.get("doc_id")
                            if doc_id and doc_id not in seen_ids:
                                seen_ids.add(doc_id)
                                sources.append(
                                    {
                                        "type": "document",
                                        "doc_id": doc_id,
                                        "chunk_id": item.get("chunk_id"),
                                        "title": item.get("title", "Unknown"),
                                        "distance": item.get("distance"),
                                    }
                                )

        return sources

    def query(
        self,
        question: str,
        strategy: Optional[str] = None,
        conversation_history: Optional[List] = None,
    ) -> Dict:
        """
        Query Agentic RAG system synchronously.

        Args:
            question: User question
            strategy: Optional search strategy override
            conversation_history: Optional conversation history

        Returns:
            Dictionary with answer, sources, tool_calls, and metadata
        """
        try:
            # Override strategy if provided
            if strategy:
                self.agentic_search_service.default_strategy_name = strategy

            # Execute agent query
            result = self.executor.execute(question, conversation_history)

            # Extract sources from tool calls
            sources = self._extract_sources(result.get("tool_calls", []))

            return {
                "answer": result.get("answer", ""),
                "sources": sources,
                "tool_calls": result.get("tool_calls", []),
                "metadata": {
                    "iterations": result.get("iterations", 0),
                    "max_iterations_reached": result.get("max_iterations_reached", False),
                    "strategy": strategy or self.default_strategy,
                    "tool_call_count": len(result.get("tool_calls", [])),
                },
            }

        except Exception as e:
            logger.error(f"Error in Agentic RAG query: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "tool_calls": [],
                "metadata": {"error": str(e)},
            }

    def stream_query(
        self,
        question: str,
        strategy: Optional[str] = None,
        conversation_history: Optional[List] = None,
    ) -> Iterator[str]:
        """
        Stream query response.

        Args:
            question: User question
            strategy: Optional search strategy override
            conversation_history: Optional conversation history

        Yields:
            Text chunks as they are generated
        """
        try:
            # Override strategy if provided
            if strategy:
                self.agentic_search_service.default_strategy_name = strategy

            # Stream execute
            for chunk in self.executor.stream_execute(question, conversation_history):
                yield chunk

        except Exception as e:
            logger.error(f"Error in Agentic RAG stream query: {e}")
            yield f"Error generating answer: {str(e)}"

    async def aquery(
        self,
        question: str,
        strategy: Optional[str] = None,
        conversation_history: Optional[List] = None,
    ) -> Dict:
        """
        Query Agentic RAG system asynchronously.

        Args:
            question: User question
            strategy: Optional search strategy override
            conversation_history: Optional conversation history

        Returns:
            Dictionary with answer, sources, tool_calls, and metadata
        """
        try:
            # Override strategy if provided
            if strategy:
                self.agentic_search_service.default_strategy_name = strategy

            # Execute agent query asynchronously
            result = await self.executor.aexecute(question, conversation_history)

            # Extract sources from tool calls
            sources = self._extract_sources(result.get("tool_calls", []))

            return {
                "answer": result.get("answer", ""),
                "sources": sources,
                "tool_calls": result.get("tool_calls", []),
                "metadata": {
                    "iterations": result.get("iterations", 0),
                    "max_iterations_reached": result.get("max_iterations_reached", False),
                    "strategy": strategy or self.default_strategy,
                    "tool_call_count": len(result.get("tool_calls", [])),
                },
            }

        except Exception as e:
            logger.error(f"Error in Agentic RAG async query: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "tool_calls": [],
                "metadata": {"error": str(e)},
            }

    async def astream_query(
        self,
        question: str,
        strategy: Optional[str] = None,
        conversation_history: Optional[List] = None,
    ) -> AsyncIterator[str]:
        """
        Stream query response asynchronously.

        Note: Full async streaming requires async tool execution support.
        For now, this executes synchronously then streams the answer.

        Args:
            question: User question
            strategy: Optional search strategy override
            conversation_history: Optional conversation history

        Yields:
            Text chunks as they are generated
        """
        try:
            # Override strategy if provided
            if strategy:
                self.agentic_search_service.default_strategy_name = strategy

            # Execute asynchronously first
            result = await self.executor.aexecute(question, conversation_history)

            # Stream the answer
            answer = result.get("answer", "")
            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                yield answer[i : i + chunk_size]

        except Exception as e:
            logger.error(f"Error in Agentic RAG async stream query: {e}")
            yield f"Error generating answer: {str(e)}"

