"""Embedding configuration and provider management."""

import logging
import os
from enum import Enum
from typing import Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Hugging Face cache directory before importing sentence_transformers
# This must be set before any Hugging Face model is loaded
# Priority: HF_HUB_CACHE > HF_CACHE_DIR (from .env) > default
if not os.getenv("HF_HUB_CACHE") and not os.getenv("HF_HOME"):
    # Check for custom cache directory in .env
    custom_cache_dir = os.getenv("HF_CACHE_DIR")
    if custom_cache_dir:
        os.environ["HF_HUB_CACHE"] = custom_cache_dir
        logger.info(f"Setting HF_HUB_CACHE from HF_CACHE_DIR: {custom_cache_dir}")
    else:
        # Default to D:\huggingface_cache\hub on Windows
        # Users can override by setting HF_HUB_CACHE or HF_CACHE_DIR in .env
        default_cache_dir = os.path.join("D:", "huggingface_cache", "hub")
        os.environ["HF_HUB_CACHE"] = default_cache_dir
        logger.info(f"Using default HF_HUB_CACHE: {default_cache_dir}")
else:
    # Log which cache directory is being used
    cache_dir = os.getenv("HF_HUB_CACHE") or os.getenv("HF_HOME")
    logger.info(f"Using Hugging Face cache directory: {cache_dir}")

# Model dimension mapping for common embedding models
# This helps prevent dimension mismatches
MODEL_DIMENSIONS: Dict[str, int] = {
    # BGE models (Chinese)
    "BAAI/bge-small-zh-v1.5": 512,
    "BAAI/bge-base-zh-v1.5": 768,
    "BAAI/bge-large-zh-v1.5": 1024,
    # BGE models (English)
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
    # BGE Multilingual models (支持100+语言)
    "BAAI/bge-m3": 1024,  # 多语言模型，支持中英文等多种语言
    # MiniLM models
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    # Multilingual E5 models
    "intfloat/multilingual-e5-base": 768,  # 多语言模型
    "intfloat/multilingual-e5-large": 1024,  # 多语言模型
    # Code embedding models (代码专用模型)
    "microsoft/codebert-base": 768,  # CodeBERT，支持多种编程语言
    "Salesforce/codet5-base": 768,  # CodeT5，代码理解和生成
    "microsoft/unilm-base-cased": 768,  # UniLM，支持代码和文本
    # OpenAI models (variable dimensions)
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    # Cloud API models (dimensions may vary, set via env if needed)
    "embedding-2": 1024,  # Zhipu
    "text-embedding": 1024,  # Baidu
    "text-embedding-v2": 1536,  # Alibaba
}

# Default model: upgraded to bge-base-zh-v1.5 for better performance
# This is a balance between performance and resource consumption
# NOTE: This is only used as a fallback if EMBEDDING_MODEL is not set in .env
# Users should explicitly set EMBEDDING_MODEL in .env file
DEFAULT_MODEL = "BAAI/bge-base-zh-v1.5"
DEFAULT_DIMENSION = 768


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    LOCAL = "local"  # 本地模型（sentence-transformers）
    ZHIPU = "zhipu"  # 智谱AI
    BAIDU = "baidu"  # 百度文心
    ALIBABA = "alibaba"  # 阿里通义
    OPENAI = "openai"


class EmbeddingConfig:
    """Embedding configuration manager with unified model settings."""

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
            # 本地模型配置 - 必须从 .env 文件设置
            model_name_env = os.getenv("EMBEDDING_MODEL")
            if not model_name_env:
                logger.error(
                    "EMBEDDING_MODEL is not set in .env file!\n"
                    "Please add EMBEDDING_MODEL to your .env file.\n"
                    "Example: EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5\n"
                    "See docs/CHINESE_MODELS_CONFIG.md for available models."
                )
                raise ValueError(
                    "EMBEDDING_MODEL must be set in .env file. "
                    "Please add EMBEDDING_MODEL=<model-name> to your .env file."
                )
            self.model_name = model_name_env
            self.device = os.getenv("EMBEDDING_DEVICE", "auto")
            # Get dimension from mapping or use default
            self.dimension = self._get_model_dimension(self.model_name)
        elif self.provider == EmbeddingProvider.ZHIPU:
            self.api_key = os.getenv("ZHIPU_API_KEY", "")
            self.api_base = os.getenv(
                "ZHIPU_EMBEDDING_API_BASE",
                "https://open.bigmodel.cn/api/paas/v4/embeddings",
            )
            self.model = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-2")
            self.dimension = self._get_model_dimension(
                self.model, default=MODEL_DIMENSIONS.get("embedding-2", 1024)
            )
        elif self.provider == EmbeddingProvider.BAIDU:
            self.api_key = os.getenv("BAIDU_API_KEY", "")
            self.api_secret = os.getenv("BAIDU_API_SECRET", "")
            self.api_base = os.getenv(
                "BAIDU_EMBEDDING_API_BASE",
                "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings",
            )
            self.model = os.getenv("BAIDU_EMBEDDING_MODEL", "text-embedding")
            self.dimension = self._get_model_dimension(
                self.model, default=MODEL_DIMENSIONS.get("text-embedding", 1024)
            )
        elif self.provider == EmbeddingProvider.ALIBABA:
            self.api_key = os.getenv("ALIBABA_API_KEY", "")
            self.api_base = os.getenv(
                "ALIBABA_EMBEDDING_API_BASE",
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
            )
            self.model = os.getenv("ALIBABA_EMBEDDING_MODEL", "text-embedding-v2")
            self.dimension = self._get_model_dimension(
                self.model, default=MODEL_DIMENSIONS.get("text-embedding-v2", 1536)
            )
        elif self.provider == EmbeddingProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            self.dimension = self._get_model_dimension(
                self.model,
                default=MODEL_DIMENSIONS.get("text-embedding-3-small", 1536),
            )

        # Validate configuration
        self._validate()

    def _get_model_dimension(self, model_name: str, default: Optional[int] = None) -> int:
        """
        Get embedding dimension for a model.

        Args:
            model_name: Name of the embedding model
            default: Default dimension if model not in mapping

        Returns:
            Embedding dimension
        """
        dimension = MODEL_DIMENSIONS.get(model_name, default)
        if dimension is None:
            logger.warning(
                f"Unknown model dimension for '{model_name}'. "
                f"Using default {DEFAULT_DIMENSION}. "
                "Consider adding it to MODEL_DIMENSIONS mapping."
            )
            return DEFAULT_DIMENSION
        return dimension

    def _validate(self):
        """Validate configuration."""
        if self.provider != EmbeddingProvider.LOCAL and not hasattr(
            self, "api_key"
        ):
            logger.warning(
                f"No API key found for {self.provider.value}. "
                "Please set the appropriate API key in .env file."
            )

    def get_model_name(self) -> str:
        """
        Get the model name for the current provider.

        Returns:
            Model name string
        """
        if self.provider == EmbeddingProvider.LOCAL:
            return self.model_name
        return self.model

    def get_dimension(self) -> int:
        """
        Get the embedding dimension for the current model.

        Returns:
            Embedding dimension
        """
        return self.dimension

    def __repr__(self) -> str:
        """String representation."""
        model_name = self.get_model_name()
        return (
            f"EmbeddingConfig(provider={self.provider.value}, "
            f"model={model_name}, dimension={self.dimension})"
        )


# Global embedding configuration instance
embedding_config = EmbeddingConfig()

