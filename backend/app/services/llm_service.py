"""LLM service for text generation using LangChain."""

import logging
from typing import AsyncIterator, Iterator, Optional

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

