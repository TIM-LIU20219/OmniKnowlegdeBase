"""System API routes."""

import logging
from typing import Dict, List

from fastapi import APIRouter

from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])


def _get_unique_documents(vector_service: VectorService) -> dict:
    """Get unique documents from vector store."""
    collection_name = vector_service.collection_names["documents"]
    collection = vector_service.get_or_create_collection(collection_name)

    results = collection.get(include=["metadatas"])

    if not results or not results.get("ids"):
        return {}

    metadatas = results.get("metadatas", [])
    unique_docs = {}

    for metadata in metadatas:
        doc_id = metadata.get("doc_id")
        if doc_id and doc_id not in unique_docs:
            unique_docs[doc_id] = metadata

    return unique_docs


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    vector_service = VectorService()

    # Get document count
    unique_docs = _get_unique_documents(vector_service)
    total_documents = len(unique_docs)

    # Get total vector count (chunks)
    collection_name = vector_service.collection_names["documents"]
    collection = vector_service.get_or_create_collection(collection_name)
    total_vectors = collection.count()

    # Get collections
    collections = vector_service.list_collections()
    collection_stats = []
    for coll_name in collections:
        coll = vector_service.get_or_create_collection(coll_name)
        count = coll.count()
        collection_stats.append({"name": coll_name, "count": count})

    # Get notes count (from SQLite)
    try:
        from backend.app.services.note_metadata_service import NoteMetadataService
        note_service = NoteMetadataService()
        all_notes = note_service.get_all_notes()
        total_notes = len(all_notes)
    except Exception as e:
        logger.warning(f"Error getting notes count: {e}")
        total_notes = 0

    return {
        "total_documents": total_documents,
        "total_notes": total_notes,
        "total_vectors": total_vectors,
        "collections": collection_stats,
    }

