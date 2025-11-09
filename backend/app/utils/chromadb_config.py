"""ChromaDB configuration module."""

import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from backend.app.utils.filesystem import BASE_DIR

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ChromaDBConfig:
    """Configuration manager for ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        anonymized_telemetry: bool = False,
    ):
        """
        Initialize ChromaDB configuration.

        Args:
            persist_directory: Directory to persist ChromaDB data.
                              If None, uses CHROMA_DB_DIR env var or default to BASE_DIR/chroma_db
            anonymized_telemetry: Whether to anonymize telemetry data
        """
        # Get persist directory from env or use default
        if persist_directory is None:
            env_path = os.getenv("CHROMA_DB_DIR")
            if env_path:
                # If env var is set, use it (could be absolute or relative)
                persist_directory = Path(env_path)
                if not persist_directory.is_absolute():
                    # If relative, make it relative to project root
                    persist_directory = BASE_DIR / persist_directory
            else:
                # Default: use absolute path based on project root
                persist_directory = BASE_DIR / "chroma_db"
        else:
            # If provided, convert to Path
            persist_directory = Path(persist_directory)
            if not persist_directory.is_absolute():
                # If relative, make it relative to project root
                persist_directory = BASE_DIR / persist_directory

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.anonymized_telemetry = anonymized_telemetry

        # Collection names
        self.documents_collection = os.getenv(
            "CHROMA_DOCUMENTS_COLLECTION", "documents"
        )
        self.notes_collection = os.getenv("CHROMA_NOTES_COLLECTION", "notes")

        logger.info(f"ChromaDB config initialized: persist_dir={self.persist_directory}")

    def get_client(self) -> chromadb.Client:
        """
        Get ChromaDB client instance.

        Returns:
            ChromaDB PersistentClient instance
        """
        return chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=self.anonymized_telemetry),
        )

    def get_collection_names(self) -> dict[str, str]:
        """
        Get collection names configuration.

        Returns:
            Dictionary with collection names
        """
        return {
            "documents": self.documents_collection,
            "notes": self.notes_collection,
        }


# Global ChromaDB configuration instance
chromadb_config = ChromaDBConfig()

