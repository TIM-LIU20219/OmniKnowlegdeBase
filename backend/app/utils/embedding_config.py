"""Embedding configuration and provider management."""

import logging
import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    LOCAL = "local"  # 本地模型（sentence-transformers）
    ZHIPU = "zhipu"  # 智谱AI
    BAIDU = "baidu"  # 百度文心
    ALIBABA = "alibaba"  # 阿里通义
    OPENAI = "openai"


class EmbeddingConfig:
    """Embedding configuration manager."""

    def __init__(self):
        """Initialize embedding configuration from environment variables."""
        # Provider selection
        provider_str = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        try:
            self.provider = EmbeddingProvider(provider_str)
        except ValueError:
            logger.warning(
                f"Invalid EMBEDDING_PROVIDER '{provider_str}', defaulting to local"
            )
            self.provider = EmbeddingProvider.LOCAL

        # Load provider-specific configuration
        if self.provider == EmbeddingProvider.LOCAL:
            # 本地模型配置
            self.model_name = os.getenv(
                "EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"
            )  # 默认使用中文模型
            self.device = os.getenv("EMBEDDING_DEVICE", "auto")
        elif self.provider == EmbeddingProvider.ZHIPU:
            self.api_key = os.getenv("ZHIPU_API_KEY", "")
            self.api_base = os.getenv(
                "ZHIPU_EMBEDDING_API_BASE",
                "https://open.bigmodel.cn/api/paas/v4/embeddings",
            )
            self.model = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-2")
        elif self.provider == EmbeddingProvider.BAIDU:
            self.api_key = os.getenv("BAIDU_API_KEY", "")
            self.api_secret = os.getenv("BAIDU_API_SECRET", "")
            self.api_base = os.getenv(
                "BAIDU_EMBEDDING_API_BASE",
                "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings",
            )
            self.model = os.getenv("BAIDU_EMBEDDING_MODEL", "text-embedding")
        elif self.provider == EmbeddingProvider.ALIBABA:
            self.api_key = os.getenv("ALIBABA_API_KEY", "")
            self.api_base = os.getenv(
                "ALIBABA_EMBEDDING_API_BASE",
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
            )
            self.model = os.getenv("ALIBABA_EMBEDDING_MODEL", "text-embedding-v2")
        elif self.provider == EmbeddingProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate configuration."""
        if self.provider != EmbeddingProvider.LOCAL and not hasattr(
            self, "api_key"
        ):
            logger.warning(
                f"No API key found for {self.provider.value}. "
                "Please set the appropriate API key in .env file."
            )

    def __repr__(self) -> str:
        """String representation."""
        if self.provider == EmbeddingProvider.LOCAL:
            return (
                f"EmbeddingConfig(provider={self.provider.value}, "
                f"model={self.model_name})"
            )
        else:
            return (
                f"EmbeddingConfig(provider={self.provider.value}, "
                f"model={self.model})"
            )


# Global embedding configuration instance
embedding_config = EmbeddingConfig()

