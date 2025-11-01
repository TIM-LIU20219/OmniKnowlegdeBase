"""Vector store service for ChromaDB integration."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector storage with ChromaDB."""

    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        logger.info(f"Initialized ChromaDB client at {self.persist_directory}")

    def get_or_create_collection(
        self, name: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Get or create a ChromaDB collection.

        Args:
            name: Collection name
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection object
        """
        try:
            collection = self.client.get_or_create_collection(
                name=name, metadata=metadata or {}
            )
            logger.info(f"Collection '{name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection '{name}': {e}")
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ):
        """
        Add documents to a collection.

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            ids: List of document IDs
            metadatas: Optional list of metadata dictionaries
            embeddings: Optional pre-computed embeddings
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            if embeddings:
                collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            else:
                collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                )
            logger.info(f"Added {len(documents)} documents to '{collection_name}'")
        except Exception as e:
            logger.error(f"Error adding documents to '{collection_name}': {e}")
            raise

    def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ):
        """
        Query a collection.

        Args:
            collection_name: Name of the collection
            query_texts: List of query texts
            query_embeddings: Optional pre-computed query embeddings
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Query results
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            if query_embeddings:
                results = collection.query(
                    query_embeddings=query_embeddings,
                    n_results=n_results,
                    where=where,
                )
            else:
                results = collection.query(
                    query_texts=query_texts,
                    n_results=n_results,
                    where=where,
                )
            logger.info(
                f"Query on '{collection_name}' returned {len(results.get('ids', [[]])[0])} results"
            )
            return results
        except Exception as e:
            logger.error(f"Error querying '{collection_name}': {e}")
            raise

    def delete_collection(self, name: str):
        """
        Delete a collection.

        Args:
            name: Collection name
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            logger.error(f"Error deleting collection '{name}': {e}")
            raise

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            names = [col.name for col in collections]
            logger.info(f"Found {len(names)} collections")
            return names
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            raise

