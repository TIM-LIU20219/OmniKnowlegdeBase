"""LLM configuration and provider management."""

import logging
import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    OPENAI = "openai"


class LLMConfig:
    """LLM configuration manager."""

    def __init__(self):
        """Initialize LLM configuration from environment variables."""
        # Provider selection
        provider_str = os.getenv("LLM_PROVIDER", "deepseek").lower()
        try:
            self.provider = LLMProvider(provider_str)
        except ValueError:
            logger.warning(
                f"Invalid LLM_PROVIDER '{provider_str}', defaulting to deepseek"
            )
            self.provider = LLMProvider.DEEPSEEK

        # Load provider-specific configuration
        if self.provider == LLMProvider.DEEPSEEK:
            self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
            self.api_base = os.getenv(
                "DEEPSEEK_API_BASE", "https://api.deepseek.com"
            )
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif self.provider == LLMProvider.OPENROUTER:
            self.api_key = os.getenv("OPENROUTER_API_KEY", "")
            self.api_base = "https://openrouter.ai/api/v1"
            self.model = os.getenv(
                "OPENROUTER_MODEL", "deepseek/deepseek-chat"
            )
        elif self.provider == LLMProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            self.api_base = "https://api.openai.com/v1"
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        # General LLM settings
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate configuration."""
        if not self.api_key:
            logger.warning(
                f"No API key found for {self.provider.value}. "
                "Please set the appropriate API key in .env file."
            )

    def get_langchain_config(self) -> dict:
        """
        Get configuration dictionary for LangChain.

        Returns:
            Configuration dictionary
        """
        config = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

        if self.provider == LLMProvider.DEEPSEEK:
            config["openai_api_key"] = self.api_key
            config["openai_api_base"] = self.api_base
        elif self.provider == LLMProvider.OPENROUTER:
            config["openai_api_key"] = self.api_key
            config["openai_api_base"] = self.api_base
            config["headers"] = {"HTTP-Referer": self.api_base}
        elif self.provider == LLMProvider.OPENAI:
            config["openai_api_key"] = self.api_key
            config["openai_api_base"] = self.api_base

        return config

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LLMConfig(provider={self.provider.value}, "
            f"model={self.model}, "
            f"api_base={self.api_base})"
        )


# Global LLM configuration instance
llm_config = LLMConfig()

