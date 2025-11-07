"""Agentic Search service for intelligent retrieval using LLM tool calling."""

import logging
from typing import Any, Dict, List, Optional

from backend.app.services.agent_tools import AgentTools
from backend.app.services.search_strategy import (
    HybridStrategy,
    NoteFirstStrategy,
    SearchStrategy,
)

logger = logging.getLogger(__name__)


class AgenticSearchService:
    """
    Agentic Search service that uses LLM tool calling for intelligent retrieval.

    This service allows the LLM to autonomously decide which search tools to use
    and in what order, enabling more flexible and context-aware retrieval.
    """

    def __init__(
        self,
        tools: AgentTools,
        default_strategy: Optional[str] = None,
    ):
        """
        Initialize Agentic Search service.

        Args:
            tools: AgentTools instance
            default_strategy: Optional default strategy name ("note-first", "hybrid", etc.)
        """
        self.tools = tools
        self.default_strategy_name = default_strategy or "hybrid"

        # Initialize strategies
        self.strategies = {
            "note-first": NoteFirstStrategy(tools),
            "hybrid": HybridStrategy(tools),
        }

        logger.info(f"Initialized AgenticSearchService with strategy: {self.default_strategy_name}")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM function calling.

        Returns:
            List of tool definitions in OpenAI format
        """
        return self.tools.get_tool_definitions()

    def search_with_strategy(
        self,
        query: str,
        strategy_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search using a specific strategy.

        Args:
            query: Search query
            strategy_name: Strategy name ("note-first", "hybrid", etc.)
            context: Optional context from previous steps

        Returns:
            List of search results
        """
        strategy_name = strategy_name or self.default_strategy_name

        if strategy_name not in self.strategies:
            logger.warning(f"Unknown strategy '{strategy_name}', using default")
            strategy_name = self.default_strategy_name

        strategy = self.strategies[strategy_name]
        results = strategy.execute(query, context)

        logger.info(f"Strategy '{strategy_name}' returned {len(results)} results")
        return results

    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a readable string for LLM context.

        Args:
            results: List of search result dictionaries

        Returns:
            Formatted string representation of results
        """
        if not results:
            return "No results found."

        formatted_parts = []
        for i, result in enumerate(results, 1):
            part = f"[Result {i}]\n"

            # Note results
            if "note_id" in result:
                part += f"Note ID: {result['note_id']}\n"
                part += f"Title: {result.get('title', 'Unknown')}\n"
                if "tags" in result:
                    part += f"Tags: {', '.join(result['tags'])}\n"
                if "links" in result:
                    part += f"Links: {', '.join(result['links'])}\n"
                if "content" in result:
                    content = result["content"]
                    # Truncate long content
                    if len(content) > 1000:
                        content = content[:1000] + "..."
                    part += f"Content:\n{content}\n"

            # Document chunk results
            elif "doc_id" in result:
                part += f"Document ID: {result['doc_id']}\n"
                part += f"Title: {result.get('title', 'Unknown')}\n"
                part += f"Source: {result.get('source', 'unknown')}\n"
                if "text" in result:
                    text = result["text"]
                    # Truncate long text
                    if len(text) > 1000:
                        text = text[:1000] + "..."
                    part += f"Text:\n{text}\n"

            formatted_parts.append(part)

        return "\n".join(formatted_parts)

    def execute_tool_call(
        self, tool_name: str, tool_args: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool call directly.

        Args:
            tool_name: Name of the tool to call
            tool_args: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            result = self.tools.call_tool(tool_name, **tool_args)
            logger.debug(f"Executed tool '{tool_name}' with args {tool_args}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return {"error": str(e)}

    def get_search_context(
        self, query: str, max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Get search context for a query using default strategy.

        This is a convenience method that executes search and formats results.

        Args:
            query: Search query
            max_results: Maximum number of results to include

        Returns:
            Dictionary with formatted context and raw results
        """
        results = self.search_with_strategy(query)
        results = results[:max_results]

        formatted_context = self.format_search_results(results)

        return {
            "query": query,
            "results": results,
            "formatted_context": formatted_context,
            "result_count": len(results),
        }

