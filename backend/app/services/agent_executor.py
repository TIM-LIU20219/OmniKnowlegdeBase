"""Agent executor for managing multi-turn conversations and tool calling loops."""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.app.services.agentic_search_service import AgenticSearchService
from backend.app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Agent executor that manages multi-turn conversations and tool calling loops.

    This executor handles the ReAct-style loop:
    1. LLM receives user query
    2. LLM decides which tools to call
    3. Execute tools and get results
    4. Send results back to LLM
    5. Repeat until LLM provides final answer or max iterations reached
    """

    def __init__(
        self,
        llm_service: LLMService,
        agentic_search_service: AgenticSearchService,
        max_iterations: int = 5,
    ):
        """
        Initialize agent executor.

        Args:
            llm_service: LLMService instance with function calling support
            agentic_search_service: AgenticSearchService instance
            max_iterations: Maximum number of tool calling iterations
        """
        self.llm_service = llm_service
        self.agentic_search_service = agentic_search_service
        self.max_iterations = max_iterations

        # Get tool definitions
        self.tools = agentic_search_service.get_tool_definitions()

        logger.info(
            f"Initialized AgentExecutor with {len(self.tools)} tools, "
            f"max_iterations={max_iterations}"
        )

    def execute(
        self,
        query: str,
        conversation_history: Optional[List[BaseMessage]] = None,
    ) -> Dict[str, Any]:
        """
        Execute agent query with tool calling loop.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Returns:
            Dictionary with:
            - answer: Final answer from LLM
            - tool_calls: List of tool calls made
            - iterations: Number of iterations
            - messages: Full conversation messages
        """
        # Initialize conversation
        messages: List[BaseMessage] = conversation_history or []
        messages.append(HumanMessage(content=query))

        tool_calls_made = []
        iterations = 0

        try:
            while iterations < self.max_iterations:
                iterations += 1
                logger.debug(f"Agent iteration {iterations}/{self.max_iterations}")

                # Invoke LLM with tools
                response = self.llm_service.invoke_with_tools(messages, self.tools)

                # Add response to messages
                messages.append(response)

                # Check if LLM wants to call tools
                if not self.llm_service.has_tool_calls(response):
                    # No tool calls, LLM provided final answer
                    answer = response.content if hasattr(response, "content") else str(response)
                    logger.info(f"Agent completed after {iterations} iterations")
                    return {
                        "answer": answer,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                        "messages": messages,
                    }

                # Extract tool calls
                tool_calls = self.llm_service.get_tool_calls(response)
                logger.debug(f"LLM requested {len(tool_calls)} tool calls")

                # Execute each tool call
                for tool_call in tool_calls:
                    # Handle different tool_call formats
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "") or tool_call.get("function", {}).get("name", "")
                        tool_args_raw = tool_call.get("args", {}) or tool_call.get("function", {}).get("arguments", {})
                        tool_call_id = tool_call.get("id", "") or tool_call.get("tool_call_id", "")
                        
                        # Parse args if it's a string (JSON)
                        if isinstance(tool_args_raw, str):
                            import json
                            try:
                                tool_args = json.loads(tool_args_raw)
                            except json.JSONDecodeError:
                                tool_args = {}
                        else:
                            tool_args = tool_args_raw or {}
                    else:
                        # Fallback for other formats
                        tool_name = getattr(tool_call, "name", "") or getattr(tool_call, "function", {}).get("name", "")
                        tool_args = getattr(tool_call, "args", {}) or {}
                        tool_call_id = getattr(tool_call, "id", "") or ""

                    logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

                    # Execute tool
                    try:
                        result = self.agentic_search_service.execute_tool_call(
                            tool_name, tool_args
                        )

                        # Create tool message
                        tool_message = self.llm_service.create_tool_message(
                            tool_call_id, tool_name, result
                        )
                        messages.append(tool_message)

                        # Record tool call
                        tool_calls_made.append(
                            {
                                "iteration": iterations,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "result": result,
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        # Create error tool message
                        error_message = self.llm_service.create_tool_message(
                            tool_call_id,
                            tool_name,
                            {"error": str(e)},
                        )
                        messages.append(error_message)

            # Max iterations reached
            logger.warning(f"Agent reached max iterations ({self.max_iterations})")
            final_response = messages[-1] if messages else None
            answer = (
                final_response.content
                if final_response and hasattr(final_response, "content")
                else "I reached the maximum number of iterations. Please try a simpler query."
            )

            return {
                "answer": answer,
                "tool_calls": tool_calls_made,
                "iterations": iterations,
                "messages": messages,
                "max_iterations_reached": True,
            }

        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            return {
                "answer": f"Error during agent execution: {str(e)}",
                "tool_calls": tool_calls_made,
                "iterations": iterations,
                "messages": messages,
                "error": str(e),
            }

    async def aexecute(
        self,
        query: str,
        conversation_history: Optional[List[BaseMessage]] = None,
    ) -> Dict[str, Any]:
        """
        Execute agent query asynchronously with tool calling loop.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Returns:
            Dictionary with answer, tool_calls, iterations, and messages
        """
        # Initialize conversation
        messages: List[BaseMessage] = conversation_history or []
        messages.append(HumanMessage(content=query))

        tool_calls_made = []
        iterations = 0

        try:
            while iterations < self.max_iterations:
                iterations += 1
                logger.debug(f"Agent iteration {iterations}/{self.max_iterations}")

                # Invoke LLM with tools
                response = await self.llm_service.ainvoke_with_tools(messages, self.tools)

                # Add response to messages
                messages.append(response)

                # Check if LLM wants to call tools
                if not self.llm_service.has_tool_calls(response):
                    # No tool calls, LLM provided final answer
                    answer = response.content if hasattr(response, "content") else str(response)
                    logger.info(f"Agent completed after {iterations} iterations")
                    return {
                        "answer": answer,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                        "messages": messages,
                    }

                # Extract tool calls
                tool_calls = self.llm_service.get_tool_calls(response)
                logger.debug(f"LLM requested {len(tool_calls)} tool calls")

                # Execute each tool call
                for tool_call in tool_calls:
                    # Handle different tool_call formats
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "") or tool_call.get("function", {}).get("name", "")
                        tool_args_raw = tool_call.get("args", {}) or tool_call.get("function", {}).get("arguments", {})
                        tool_call_id = tool_call.get("id", "") or tool_call.get("tool_call_id", "")
                        
                        # Parse args if it's a string (JSON)
                        if isinstance(tool_args_raw, str):
                            import json
                            try:
                                tool_args = json.loads(tool_args_raw)
                            except json.JSONDecodeError:
                                tool_args = {}
                        else:
                            tool_args = tool_args_raw or {}
                    else:
                        # Fallback for other formats
                        tool_name = getattr(tool_call, "name", "") or getattr(tool_call, "function", {}).get("name", "")
                        tool_args = getattr(tool_call, "args", {}) or {}
                        tool_call_id = getattr(tool_call, "id", "") or ""

                    logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

                    # Execute tool
                    try:
                        result = self.agentic_search_service.execute_tool_call(
                            tool_name, tool_args
                        )

                        # Create tool message
                        tool_message = self.llm_service.create_tool_message(
                            tool_call_id, tool_name, result
                        )
                        messages.append(tool_message)

                        # Record tool call
                        tool_calls_made.append(
                            {
                                "iteration": iterations,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "result": result,
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        # Create error tool message
                        error_message = self.llm_service.create_tool_message(
                            tool_call_id,
                            tool_name,
                            {"error": str(e)},
                        )
                        messages.append(error_message)

            # Max iterations reached
            logger.warning(f"Agent reached max iterations ({self.max_iterations})")
            final_response = messages[-1] if messages else None
            answer = (
                final_response.content
                if final_response and hasattr(final_response, "content")
                else "I reached the maximum number of iterations. Please try a simpler query."
            )

            return {
                "answer": answer,
                "tool_calls": tool_calls_made,
                "iterations": iterations,
                "messages": messages,
                "max_iterations_reached": True,
            }

        except Exception as e:
            logger.error(f"Error in async agent execution: {e}")
            return {
                "answer": f"Error during agent execution: {str(e)}",
                "tool_calls": tool_calls_made,
                "iterations": iterations,
                "messages": messages,
                "error": str(e),
            }

    def stream_execute(
        self,
        query: str,
        conversation_history: Optional[List[BaseMessage]] = None,
    ):
        """
        Execute agent query with streaming response.

        Note: Streaming with tool calling is complex. This implementation
        executes tools first, then streams the final answer.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Yields:
            Text chunks from final answer
        """
        # Execute tool calling loop first
        result = self.execute(query, conversation_history)

        # Stream the final answer
        answer = result.get("answer", "")
        # Split answer into chunks for streaming effect
        chunk_size = 50
        for i in range(0, len(answer), chunk_size):
            yield answer[i : i + chunk_size]

