"""Workflow orchestrator for managing different note generation modes."""

import logging
from typing import Dict, Optional, Tuple

from backend.app.services.note_generation_service import NoteGenerationService

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Workflow orchestrator that detects user input mode and routes to appropriate workflow.
    
    Supports modes:
    - /new: Generate note using LLM's own knowledge, retrieval only for similarity review
    - /ask: Generate note using RAG retrieval first, then generate based on retrieved context
    - /enhance: Enhance existing note content (future implementation)
    """

    def __init__(
        self,
        note_generation_service: Optional[NoteGenerationService] = None,
    ):
        """
        Initialize workflow orchestrator.

        Args:
            note_generation_service: Optional NoteGenerationService instance
        """
        self.note_generation_service = (
            note_generation_service or NoteGenerationService()
        )

        logger.info("Initialized WorkflowOrchestrator")

    def detect_mode(self, query: str) -> Tuple[str, str]:
        """
        Detect mode from user input and extract actual query.

        Args:
            query: User input query

        Returns:
            Tuple of (mode, actual_query)
            mode: "/new", "/ask", "/enhance", or "default"
            actual_query: Query content without mode prefix
        """
        query = query.strip()

        # Check for /new mode
        if query.startswith("/new"):
            actual_query = query[4:].strip()
            if actual_query:
                return "/new", actual_query
            else:
                logger.warning("Empty query after /new, using default mode")
                return "default", query

        # Check for /ask mode
        if query.startswith("/ask"):
            actual_query = query[4:].strip()
            if actual_query:
                return "/ask", actual_query
            else:
                logger.warning("Empty query after /ask, using default mode")
                return "default", query

        # Check for /enhance mode
        if query.startswith("/enhance"):
            actual_query = query[8:].strip()
            if actual_query:
                return "/enhance", actual_query
            else:
                logger.warning("Empty query after /enhance, using default mode")
                return "default", query

        # Default mode: try to infer from context
        # For now, default to /ask (RAG mode)
        return "default", query

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Execute workflow based on detected mode.

        Args:
            query: User input query
            session_id: Optional session ID for conversation history
            **kwargs: Additional arguments passed to workflow

        Returns:
            Dictionary with workflow execution result
        """
        mode, actual_query = self.detect_mode(query)

        logger.info(f"Executing workflow: mode={mode}, query={actual_query[:50]}...")

        try:
            if mode == "/new":
                return self._execute_new_mode(actual_query, **kwargs)
            elif mode == "/ask":
                return self._execute_ask_mode(actual_query, **kwargs)
            elif mode == "/enhance":
                return self._execute_enhance_mode(actual_query, **kwargs)
            else:
                # Default mode: use /ask (RAG mode)
                logger.info("Using default mode (/ask)")
                return self._execute_ask_mode(actual_query, **kwargs)

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                "mode": mode,
                "error": str(e),
                "content": "",
                "title": "",
                "suggestions": "",
                "similar_notes": [],
                "added_links": [],
            }

    def _execute_new_mode(self, topic: str, **kwargs) -> Dict:
        """
        Execute /new mode: Generate note using LLM's own knowledge.

        Args:
            topic: Topic or question for note generation
            **kwargs: Additional arguments

        Returns:
            Dictionary with generation result
        """
        result = self.note_generation_service.generate_with_llm_knowledge(
            topic=topic,
            **kwargs
        )
        result["mode"] = "/new"
        return result

    def _execute_ask_mode(self, question: str, **kwargs) -> Dict:
        """
        Execute /ask mode: Generate note using RAG retrieval first.

        Args:
            question: Question for RAG retrieval and note generation
            **kwargs: Additional arguments

        Returns:
            Dictionary with generation result
        """
        result = self.note_generation_service.generate_with_rag(
            question=question,
            **kwargs
        )
        result["mode"] = "/ask"
        return result

    def _execute_enhance_mode(self, content: str, **kwargs) -> Dict:
        """
        Execute /enhance mode: Enhance existing note content.

        Args:
            content: Existing note content to enhance
            **kwargs: Additional arguments

        Returns:
            Dictionary with enhancement result
        """
        # TODO: Implement enhance mode
        logger.warning("/enhance mode not yet implemented")
        return {
            "mode": "/enhance",
            "error": "/enhance mode not yet implemented",
            "content": content,
            "title": "",
            "suggestions": "",
            "similar_notes": [],
            "added_links": [],
        }

