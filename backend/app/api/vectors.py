"""Vector store management API routes."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from backend.app.api.schemas import CollectionStatsResponse, VectorQueryRequest, VectorQueryResult
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vectors", tags=["vectors"])


@router.get("/collections", response_model=List[str])
async def list_collections():
    """List all collections."""
    vector_service = VectorService()

    try:
        collections = vector_service.list_collections()
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{name}/stats", response_model=CollectionStatsResponse)
async def get_collection_stats(name: str):
    """Get statistics for a collection."""
    vector_service = VectorService()

    try:
        collection = vector_service.get_or_create_collection(name)
        count = collection.count()

        # Get sample metadata to understand structure
        results = collection.get(limit=min(100, count), include=["metadatas"])

        unique_documents = None
        if results and results.get("metadatas"):
            doc_ids = set()
            for metadata in results["metadatas"]:
                if "doc_id" in metadata:
                    doc_ids.add(metadata["doc_id"])
            unique_documents = len(doc_ids) if doc_ids else None

        return CollectionStatsResponse(
            collection=name,
            total_documents=count,
            unique_documents=unique_documents,
        )
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}", status_code=204)
async def delete_collection(name: str):
    """Delete a collection."""
    vector_service = VectorService()

    try:
        vector_service.delete_collection(name)
        return None
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}/documents/{doc_id}", status_code=204)
async def delete_document_from_collection(name: str, doc_id: str):
    """Delete a document from a collection."""
    vector_service = VectorService()

    try:
        vector_service.delete_document(name, doc_id)
        return None
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{name}/query", response_model=List[VectorQueryResult])
async def query_collection(name: str, request: VectorQueryRequest):
    """Query a collection with semantic search."""
    vector_service = VectorService()
    embedding_service = EmbeddingService()

    try:
        # Generate query embedding
        query_embedding = embedding_service.embed_text(request.query_text)

        # Query collection
        results = vector_service.query(
            collection_name=name,
            query_embeddings=[query_embedding],
            n_results=request.k,
        )

        if not results or not results.get("ids") or len(results["ids"][0]) == 0:
            return []

        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        query_results = []
        for i, (doc_id, doc_text, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances)
        ):
            similarity = 1.0 - distance if distance is not None else None
            query_results.append(
                VectorQueryResult(
                    rank=i + 1,
                    id=doc_id,
                    content=doc_text,
                    metadata=metadata,
                    distance=distance,
                    similarity=similarity,
                )
            )

        return query_results
    except Exception as e:
        logger.error(f"Error querying collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

