"""Vector store service for ChromaDB integration."""

import logging
from typing import Any, Dict, List, Optional

from backend.app.utils.chromadb_config import chromadb_config

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector storage with ChromaDB."""

    def __init__(self, config=None):
        """
        Initialize ChromaDB client.

        Args:
            config: Optional ChromaDBConfig instance. If None, uses global config.
        """
        self.config = config or chromadb_config
        self.client = self.config.get_client()
        self.collection_names = self.config.get_collection_names()

        logger.info(
            f"Initialized ChromaDB client at {self.config.persist_directory}"
        )

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

    def get_documents_collection(self):
        """
        Get or create the documents collection.

        Returns:
            ChromaDB collection for documents
        """
        return self.get_or_create_collection(self.collection_names["documents"])

    def get_notes_collection(self):
        """
        Get or create the notes collection.

        Returns:
            ChromaDB collection for notes
        """
        return self.get_or_create_collection(self.collection_names["notes"])

    def delete_document(self, collection_name: str, doc_id: str):
        """
        Delete a document from a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Document ID to delete
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=[doc_id])
            logger.info(f"Deleted document '{doc_id}' from '{collection_name}'")
        except Exception as e:
            logger.error(
                f"Error deleting document '{doc_id}' from '{collection_name}': {e}"
            )
            raise

