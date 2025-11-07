"""LLM service for text generation using LangChain."""

import json
import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from backend.app.utils.llm_config import LLMConfig, llm_config

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM text generation."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM service.

        Args:
            config: Optional LLMConfig instance. If None, uses global config.
        """
        self.config = config or llm_config
        self._llm: Optional[ChatOpenAI] = None

        logger.info(
            f"Initialized LLM service: provider={self.config.provider.value}, "
            f"model={self.config.model}"
        )

    @property
    def llm(self) -> ChatOpenAI:
        """
        Get or create LangChain LLM instance.

        Returns:
            ChatOpenAI instance configured with provider settings
        """
        if self._llm is None:
            try:
                langchain_config = self.config.get_langchain_config()

                # Create ChatOpenAI instance
                # LangChain's ChatOpenAI can work with OpenAI-compatible APIs
                self._llm = ChatOpenAI(
                    model_name=langchain_config["model"],
                    temperature=langchain_config["temperature"],
                    max_tokens=langchain_config["max_tokens"],
                    openai_api_key=langchain_config.get("openai_api_key"),
                    openai_api_base=langchain_config.get("openai_api_base"),
                    timeout=langchain_config.get("timeout", 60),
                )

                # Add headers for OpenRouter if needed
                if self.config.provider.value == "openrouter":
                    headers = langchain_config.get("headers", {})
                    if headers:
                        self._llm.openai_api_base = langchain_config["openai_api_base"]
                        # Note: LangChain may not directly support custom headers
                        # This is a limitation we'll work around

                logger.info("LLM instance created successfully")
            except Exception as e:
                logger.error(f"Error creating LLM instance: {e}")
                raise

        return self._llm

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Generate text synchronously.

        Args:
            prompt: Input prompt text
            **kwargs: Additional arguments for LLM invocation

        Returns:
            Generated text response
        """
        try:
            # ChatOpenAI expects a list of messages, not a string
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages, **kwargs)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Generate text as a stream.

        Args:
            prompt: Input prompt text
            **kwargs: Additional arguments for LLM invocation

        Yields:
            Text chunks as they are generated
        """
        try:
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            for chunk in self.llm.stream(messages, **kwargs):
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Error streaming text: {e}")
            raise

    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """
        Generate text asynchronously.

        Args:
            prompt: Input prompt text
            **kwargs: Additional arguments for LLM invocation

        Returns:
            Generated text response
        """
        try:
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error generating text asynchronously: {e}")
            raise

    async def astream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Generate text as an async stream.

        Args:
            prompt: Input prompt text
            **kwargs: Additional arguments for LLM invocation

        Yields:
            Text chunks as they are generated
        """
        try:
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            async for chunk in self.llm.astream(messages, **kwargs):
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Error streaming text asynchronously: {e}")
            raise

    def invoke_with_tools(
        self,
        messages: List[BaseMessage],
        tools: List[Dict[str, Any]],
        **kwargs,
    ) -> BaseMessage:
        """
        Invoke LLM with function calling tools.

        Args:
            messages: List of message objects (HumanMessage, AIMessage, ToolMessage)
            tools: List of tool definitions in OpenAI format
            **kwargs: Additional arguments for LLM invocation

        Returns:
            AIMessage with potential tool calls
        """
        try:
            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools(tools)
            
            # Invoke with messages
            response = llm_with_tools.invoke(messages, **kwargs)
            
            return response
        except Exception as e:
            logger.error(f"Error invoking LLM with tools: {e}")
            raise

    async def ainvoke_with_tools(
        self,
        messages: List[BaseMessage],
        tools: List[Dict[str, Any]],
        **kwargs,
    ) -> BaseMessage:
        """
        Invoke LLM with function calling tools asynchronously.

        Args:
            messages: List of message objects
            tools: List of tool definitions in OpenAI format
            **kwargs: Additional arguments for LLM invocation

        Returns:
            AIMessage with potential tool calls
        """
        try:
            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools(tools)
            
            # Invoke with messages
            response = await llm_with_tools.ainvoke(messages, **kwargs)
            
            return response
        except Exception as e:
            logger.error(f"Error invoking LLM with tools asynchronously: {e}")
            raise

    def has_tool_calls(self, message: BaseMessage) -> bool:
        """
        Check if a message contains tool calls.

        Args:
            message: Message to check

        Returns:
            True if message has tool calls
        """
        if isinstance(message, AIMessage):
            return hasattr(message, "tool_calls") and len(message.tool_calls) > 0
        return False

    def get_tool_calls(self, message: BaseMessage) -> List[Dict[str, Any]]:
        """
        Extract tool calls from a message.

        Args:
            message: Message containing tool calls

        Returns:
            List of tool call dictionaries
        """
        if isinstance(message, AIMessage) and hasattr(message, "tool_calls"):
            return message.tool_calls or []
        return []

    def create_tool_message(
        self, tool_call_id: str, tool_name: str, result: Any
    ) -> ToolMessage:
        """
        Create a ToolMessage from tool execution result.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool that was called
            result: Tool execution result

        Returns:
            ToolMessage instance
        """
        # Convert result to string if needed
        if isinstance(result, (dict, list)):
            content = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            content = str(result)

        return ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name,
        )

