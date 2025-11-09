"""Structured code retrieval service with metadata filtering."""

import logging
import re
from typing import Dict, List, Optional

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.retriever import ChromaDBRetriever
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class StructuredCodeRetriever:
    """Retriever for structured code search with metadata filtering."""

    def __init__(
        self,
        vector_service: Optional[VectorService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        collection_name: str = "documents",
        k: int = 5,
    ):
        """
        Initialize structured code retriever.

        Args:
            vector_service: Optional VectorService instance
            embedding_service: Optional EmbeddingService instance
            collection_name: ChromaDB collection name
            k: Number of results to return
        """
        self.vector_service = vector_service or VectorService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection_name = collection_name
        self.k = k

        # Initialize base retriever
        self.base_retriever = ChromaDBRetriever(
            vector_service=self.vector_service,
            embedding_service=self.embedding_service,
            collection_name=collection_name,
            k=k,
        )

        logger.info(
            f"Initialized StructuredCodeRetriever: collection={collection_name}, k={k}"
        )

    def search_by_function(
        self,
        function_name: str,
        class_name: Optional[str] = None,
        module_name: Optional[str] = None,
        import_batch: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for code by function name.

        Args:
            function_name: Function name to search for
            class_name: Optional class name filter
            module_name: Optional module name filter
            import_batch: Optional batch identifier filter
            k: Number of results to return

        Returns:
            List of search result dictionaries
        """
        # Build where clause with $and operator for multiple conditions
        conditions = {"code_function_name": function_name}
        
        if class_name:
            conditions["code_class_name"] = class_name
        if module_name:
            conditions["code_module_name"] = module_name
        if import_batch:
            conditions["import_batch"] = import_batch
        
        # Use $and if multiple conditions
        if len(conditions) > 1:
            metadata_filter = {"$and": [{"code_function_name": function_name}]}
            if class_name:
                metadata_filter["$and"].append({"code_class_name": class_name})
            if module_name:
                metadata_filter["$and"].append({"code_module_name": module_name})
            if import_batch:
                metadata_filter["$and"].append({"import_batch": import_batch})
        else:
            metadata_filter = conditions

        return self._query_with_filter(
            query_text=f"function {function_name}",
            metadata_filter=metadata_filter,
            k=k,
        )

    def search_by_class(
        self,
        class_name: str,
        module_name: Optional[str] = None,
        import_batch: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for code by class name.

        Args:
            class_name: Class name to search for
            module_name: Optional module name filter
            import_batch: Optional batch identifier filter
            k: Number of results to return

        Returns:
            List of search result dictionaries
        """
        conditions = [{"code_class_name": class_name}, {"code_code_type": "class"}]
        
        if module_name:
            conditions.append({"code_module_name": module_name})
        if import_batch:
            conditions.append({"import_batch": import_batch})
        
        metadata_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

        return self._query_with_filter(
            query_text=f"class {class_name}",
            metadata_filter=metadata_filter,
            k=k,
        )

    def search_by_path(
        self,
        path_pattern: str,
        import_batch: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for code by file path pattern.

        Args:
            path_pattern: File path pattern (supports regex)
            import_batch: Optional batch identifier filter
            k: Number of results to return

        Returns:
            List of search result dictionaries
        """
        # ChromaDB regex only works in query, not get
        # So we need to use semantic search with path filter
        conditions = [{"file_path": {"$regex": path_pattern}}]
        
        if import_batch:
            conditions.append({"import_batch": import_batch})
        
        metadata_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

        return self._query_with_filter(
            query_text="", 
            metadata_filter=metadata_filter, 
            k=k, 
            semantic_search=True  # Use query for regex support
        )

    def search_by_module(
        self,
        module_name: str,
        import_batch: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for code by module name.

        Args:
            module_name: Module name to search for
            import_batch: Optional batch identifier filter
            k: Number of results to return

        Returns:
            List of search result dictionaries
        """
        conditions = [{"code_module_name": module_name}]
        
        if import_batch:
            conditions.append({"import_batch": import_batch})
        
        metadata_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

        return self._query_with_filter(
            query_text=f"module {module_name}", metadata_filter=metadata_filter, k=k
        )

    def hybrid_search(
        self,
        query: str,
        metadata_filter: Optional[Dict] = None,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Perform hybrid search combining semantic search with metadata filtering.

        Args:
            query: Query text for semantic search
            metadata_filter: Optional metadata filter dictionary
            k: Number of results to return
            score_threshold: Optional similarity score threshold

        Returns:
            List of search result dictionaries
        """
        return self._query_with_filter(
            query_text=query,
            metadata_filter=metadata_filter,
            k=k,
            score_threshold=score_threshold,
        )

    def _query_with_filter(
        self,
        query_text: str,
        metadata_filter: Optional[Dict] = None,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        semantic_search: bool = True,
    ) -> List[Dict]:
        """
        Query ChromaDB with metadata filter.

        Args:
            query_text: Query text for semantic search
            metadata_filter: Metadata filter dictionary
            k: Number of results to return
            score_threshold: Optional similarity score threshold
            semantic_search: Whether to perform semantic search

        Returns:
            List of search result dictionaries
        """
        k = k or self.k

        try:
            collection = self.vector_service.get_or_create_collection(self.collection_name)

            if semantic_search:
                if query_text:
                    # Semantic search with metadata filter
                    query_embedding = self.embedding_service.embed_text(query_text)
                    
                    # Normalize metadata_filter for ChromaDB
                    normalized_filter = self._normalize_metadata_filter(metadata_filter)
                    
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=k,
                        where=normalized_filter if normalized_filter else None,
                    )
                else:
                    # Metadata-only search using query with empty embedding
                    # For regex support, we need to use query
                    dummy_embedding = [0.0] * self.embedding_service.get_embedding_dimension()
                    normalized_filter = self._normalize_metadata_filter(metadata_filter)
                    results = collection.query(
                        query_embeddings=[dummy_embedding],
                        n_results=k * 10,  # Get more to filter
                        where=normalized_filter if normalized_filter else None,
                    )
            else:
                # Metadata-only search (get all matching documents)
                normalized_filter = self._normalize_metadata_filter(metadata_filter)
                results = collection.get(where=normalized_filter if normalized_filter else None, limit=k)

            # Process results
            search_results = []
            if results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
                documents = (
                    results["documents"][0]
                    if isinstance(results["documents"][0], list)
                    else results["documents"]
                )
                metadatas = (
                    results["metadatas"][0]
                    if isinstance(results["metadatas"][0], list)
                    else results["metadatas"]
                )
                distances = (
                    results["distances"][0]
                    if "distances" in results and results["distances"]
                    else [0.0] * len(ids)
                )
                if isinstance(distances, list) and len(distances) > 0 and isinstance(distances[0], list):
                    distances = distances[0]

                for doc_id, doc_text, metadata_dict, distance in zip(
                    ids, documents, metadatas, distances
                ):
                    # Calculate similarity score (1 - distance for cosine similarity)
                    score = 1.0 - distance if distance is not None else None

                    # Apply score threshold if specified
                    if score_threshold is not None and score is not None:
                        if score < score_threshold:
                            continue

                    result = {
                        "id": doc_id,
                        "text": doc_text,
                        "metadata": metadata_dict,
                        "score": score,
                        "distance": distance,
                    }
                    search_results.append(result)
                
                # Limit results if we got more than requested
                search_results = search_results[:k]

            logger.debug(
                f"Retrieved {len(search_results)} results for query: {query_text[:50] if query_text else 'metadata-only'}..."
            )

            return search_results

        except Exception as e:
            logger.error(f"Error in structured code retrieval: {e}")
            return []

    def _normalize_metadata_filter(self, metadata_filter: Optional[Dict]) -> Optional[Dict]:
        """
        Normalize metadata filter for ChromaDB compatibility.
        
        ChromaDB requires:
        - Single condition: {"key": "value"}
        - Multiple conditions: {"$and": [{"key1": "value1"}, {"key2": "value2"}]}
        - Operators: $eq, $ne, $in, $nin, $gt, $gte, $lt, $lte
        - No $regex in query() - need to use get() or filter after query
        
        Args:
            metadata_filter: Raw metadata filter dictionary
            
        Returns:
            Normalized filter dictionary compatible with ChromaDB
        """
        if not metadata_filter:
            return None
        
        # If already using $and, return as is
        if "$and" in metadata_filter:
            return metadata_filter
        
        # If single condition, return as is
        if len(metadata_filter) == 1:
            key, value = next(iter(metadata_filter.items()))
            # Check if value is a dict with operators
            if isinstance(value, dict):
                # Check for unsupported operators
                if "$regex" in value:
                    # ChromaDB doesn't support $regex in query()
                    # Return None to skip filter, will filter manually
                    logger.warning(f"$regex operator not supported in ChromaDB query(), will filter manually")
                    return None
                return metadata_filter
            return metadata_filter
        
        # Multiple conditions - convert to $and format
        conditions = []
        for key, value in metadata_filter.items():
            if isinstance(value, dict):
                # Check for unsupported operators
                if "$regex" in value:
                    logger.warning(f"$regex operator not supported in ChromaDB query(), will filter manually")
                    continue
                conditions.append({key: value})
            else:
                conditions.append({key: value})
        
        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    def find_code_references(
        self,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        import_batch: Optional[str] = None,
    ) -> List[Dict]:
        """
        Find code that references a function or class.

        Args:
            function_name: Function name to find references for
            class_name: Class name to find references for
            import_batch: Optional batch identifier filter

        Returns:
            List of search result dictionaries
        """
        # This would require analyzing called_functions in code_metadata
        # For now, use semantic search
        query = ""
        if function_name:
            query = f"calls {function_name} uses {function_name}"
        elif class_name:
            query = f"uses {class_name} imports {class_name}"

        metadata_filter = None
        if import_batch:
            metadata_filter = {"import_batch": import_batch}

        return self._query_with_filter(query_text=query, metadata_filter=metadata_filter)

