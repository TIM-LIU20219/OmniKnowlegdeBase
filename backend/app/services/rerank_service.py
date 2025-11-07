"""Rerank service for reordering retrieval results."""

import logging
import os
from enum import Enum
from typing import List, Optional, Tuple

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RerankProvider(str, Enum):
    """Supported rerank providers."""

    LOCAL = "local"  # 本地模型（sentence-transformers）
    ZHIPU = "zhipu"  # 智谱AI
    BAIDU = "baidu"  # 百度文心
    ALIBABA = "alibaba"  # 阿里通义
    OPENAI = "openai"


class RerankService:
    """Service for reranking retrieval results."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize rerank service.

        Args:
            provider: Rerank provider name. If None, uses RERANK_PROVIDER env var.
            model_name: Model name for local provider. If None, uses RERANK_MODEL env var.
        """
        # Provider selection
        if provider is None:
            provider = os.getenv("RERANK_PROVIDER", "local").lower()

        try:
            self.provider = RerankProvider(provider)
        except ValueError:
            logger.warning(
                f"Invalid RERANK_PROVIDER '{provider}', defaulting to local"
            )
            self.provider = RerankProvider.LOCAL

        # Initialize provider-specific components
        if self.provider == RerankProvider.LOCAL:
            self._init_local(model_name)
        elif self.provider == RerankProvider.ZHIPU:
            self._init_zhipu()
        elif self.provider == RerankProvider.BAIDU:
            self._init_baidu()
        elif self.provider == RerankProvider.ALIBABA:
            self._init_alibaba()
        elif self.provider == RerankProvider.OPENAI:
            self._init_openai()

        logger.info(f"Initialized rerank service: provider={self.provider.value}")

    def _init_local(self, model_name: Optional[str] = None):
        """Initialize local rerank model."""
        try:
            from sentence_transformers import CrossEncoder

            if model_name is None:
                model_name = os.getenv(
                    "RERANK_MODEL", "BAAI/bge-reranker-base"
                )  # 默认使用中文rerank模型

            self.model_name = model_name
            self._model: Optional[CrossEncoder] = None
            logger.info(f"Local rerank model: {model_name}")
        except ImportError:
            logger.error(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            raise

    def _init_zhipu(self):
        """Initialize Zhipu rerank service."""
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.api_base = os.getenv(
            "ZHIPU_RERANK_API_BASE",
            "https://open.bigmodel.cn/api/paas/v4/rerank",
        )
        self.model = os.getenv("ZHIPU_RERANK_MODEL", "rerank")

    def _init_baidu(self):
        """Initialize Baidu rerank service."""
        self.api_key = os.getenv("BAIDU_API_KEY", "")
        self.api_secret = os.getenv("BAIDU_API_SECRET", "")

    def _init_alibaba(self):
        """Initialize Alibaba rerank service."""
        self.api_key = os.getenv("ALIBABA_API_KEY", "")
        self.api_base = os.getenv(
            "ALIBABA_RERANK_API_BASE",
            "https://dashscope.aliyuncs.com/api/v1/services/rerank/rerank",
        )
        self.model = os.getenv("ALIBABA_RERANK_MODEL", "rerank-v1")

    def _init_openai(self):
        """Initialize OpenAI rerank service."""
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    def rerank(
        self, query: str, documents: List[str], top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents based on query relevance.

        Args:
            query: Query text
            documents: List of document texts to rerank
            top_k: Number of top results to return. If None, returns all.

        Returns:
            List of (document, score) tuples, sorted by score (descending)
        """
        if not documents:
            return []

        if self.provider == RerankProvider.LOCAL:
            return self._rerank_local(query, documents, top_k)
        elif self.provider == RerankProvider.ZHIPU:
            return self._rerank_zhipu(query, documents, top_k)
        elif self.provider == RerankProvider.BAIDU:
            return self._rerank_baidu(query, documents, top_k)
        elif self.provider == RerankProvider.ALIBABA:
            return self._rerank_alibaba(query, documents, top_k)
        elif self.provider == RerankProvider.OPENAI:
            return self._rerank_openai(query, documents, top_k)
        else:
            raise ValueError(f"Unsupported rerank provider: {self.provider}")

    def _rerank_local(
        self, query: str, documents: List[str], top_k: Optional[int]
    ) -> List[Tuple[str, float]]:
        """Rerank using local CrossEncoder model."""
        if self._model is None:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading rerank model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get scores
        scores = self._model.predict(pairs)

        # Sort by score (descending)
        scored_docs = list(zip(documents, scores.tolist()))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            return scored_docs[:top_k]
        return scored_docs

    def _rerank_zhipu(
        self, query: str, documents: List[str], top_k: Optional[int]
    ) -> List[Tuple[str, float]]:
        """Rerank using Zhipu API."""
        import requests

        url = f"{self.api_base}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_k or len(documents),
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        results = response.json()
        reranked = [
            (documents[item["index"]], item["relevance_score"])
            for item in results.get("results", [])
        ]

        return reranked

    def _rerank_baidu(
        self, query: str, documents: List[str], top_k: Optional[int]
    ) -> List[Tuple[str, float]]:
        """Rerank using Baidu API."""
        # TODO: Implement Baidu rerank API
        logger.warning("Baidu rerank API not yet implemented")
        # Fallback to local model
        return self._rerank_local(query, documents, top_k)

    def _rerank_alibaba(
        self, query: str, documents: List[str], top_k: Optional[int]
    ) -> List[Tuple[str, float]]:
        """Rerank using Alibaba API."""
        import requests

        url = f"{self.api_base}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_k or len(documents),
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        results = response.json()
        reranked = [
            (documents[item["index"]], item["relevance_score"])
            for item in results.get("results", [])
        ]

        return reranked

    def _rerank_openai(
        self, query: str, documents: List[str], top_k: Optional[int]
    ) -> List[Tuple[str, float]]:
        """Rerank using OpenAI API."""
        # OpenAI doesn't have a dedicated rerank API, use embeddings + cosine similarity
        logger.warning("OpenAI rerank using embeddings fallback")
        # Fallback to local model
        return self._rerank_local(query, documents, top_k)

