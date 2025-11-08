"""Document management API routes."""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse

from backend.app.api.schemas import (
    ChunkResponse,
    DocumentCreateRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentSearchRequest,
    SearchResult,
)
from backend.app.models.metadata import DocumentMetadata
from backend.app.services.document_service import DocumentService, DuplicateDocumentError
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.retriever import ChromaDBRetriever
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


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
            try:
                unique_docs[doc_id] = DocumentMetadata.from_chromadb_metadata(metadata)
            except Exception:
                unique_docs[doc_id] = DocumentMetadata(
                    doc_id=doc_id,
                    doc_type=metadata.get("doc_type", "document"),
                    title=metadata.get("title", doc_id),
                    created_at=metadata.get("created_at", ""),
                    source=metadata.get("source", "unknown"),
                )

    return unique_docs


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    pdf_file: Optional[UploadFile] = File(None),
    markdown_file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    skip_duplicates: bool = Form(True),
    import_batch: Optional[str] = Form(None),
):
    """
    Upload a document (PDF, Markdown, or URL).
    
    Either provide a file (pdf_file or markdown_file) or a URL.
    """
    doc_service = DocumentService()

    try:
        # Handle file uploads
        if pdf_file:
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                content = await pdf_file.read()
                tmp_file.write(content)
                temp_path = Path(tmp_file.name)

            try:
                metadata = doc_service.process_and_store_pdf(
                    temp_path, skip_duplicates=skip_duplicates, import_batch=import_batch
                )
                temp_path.unlink()  # Clean up temp file
                return DocumentResponse.from_metadata(metadata)
            except DuplicateDocumentError as e:
                temp_path.unlink()
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Duplicate document: {e.existing_doc.title if e.existing_doc else 'Unknown'}",
                        "existing_doc": DocumentResponse.from_metadata(e.existing_doc).dict() if e.existing_doc else None,
                    },
                )

        elif markdown_file:
            content = (await markdown_file.read()).decode("utf-8")
            filename = markdown_file.filename or "untitled.md"

            try:
                metadata = doc_service.process_and_store_markdown(
                    content, filename, skip_duplicates=skip_duplicates, import_batch=import_batch
                )
                return DocumentResponse.from_metadata(metadata)
            except DuplicateDocumentError as e:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Duplicate document: {e.existing_doc.title if e.existing_doc else 'Unknown'}",
                        "existing_doc": DocumentResponse.from_metadata(e.existing_doc).dict() if e.existing_doc else None,
                    },
                )

        elif url:
            metadata = doc_service.process_and_store_url(url, import_batch=import_batch)
            return DocumentResponse.from_metadata(metadata)

        else:
            raise HTTPException(status_code=400, detail="Please provide a file (pdf_file or markdown_file) or URL")

    except DuplicateDocumentError:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=DocumentListResponse)
async def list_documents(by_batch: Optional[str] = Query(None, description="Filter by import batch")):
    """List all documents."""
    vector_service = VectorService()
    unique_docs = _get_unique_documents(vector_service)

    if by_batch:
        unique_docs = {
            doc_id: doc
            for doc_id, doc in unique_docs.items()
            if doc.import_batch == by_batch
        }

    documents = [DocumentResponse.from_metadata(doc) for doc in unique_docs.values()]

    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get document details."""
    vector_service = VectorService()
    unique_docs = _get_unique_documents(vector_service)

    if doc_id not in unique_docs:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    return DocumentResponse.from_metadata(unique_docs[doc_id])


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str):
    """Delete a document and all its chunks."""
    doc_service = DocumentService()

    try:
        doc_service.delete_document(doc_id)
        return None
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(doc_id: str):
    """Get all chunks for a document."""
    doc_service = DocumentService()

    try:
        chunks = doc_service.get_document_chunks(doc_id)

        if not chunks:
            raise HTTPException(status_code=404, detail=f"No chunks found for document '{doc_id}'")

        return [
            ChunkResponse(
                chunk_index=metadata.get("chunk_index", 0),
                chunk_total=metadata.get("chunk_total", 0),
                content=chunk_text,
                metadata=metadata,
            )
            for chunk_text, metadata in chunks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[SearchResult])
async def search_documents(request: DocumentSearchRequest):
    """Search documents using semantic search."""
    vector_service = VectorService()
    embedding_service = EmbeddingService()

    retriever = ChromaDBRetriever(
        vector_service=vector_service,
        embedding_service=embedding_service,
        collection_name=vector_service.collection_names["documents"],
        k=request.k,
    )

    try:
        if request.show_source_info:
            results = retriever.retrieve_with_context(request.query, include_source_info=True)
        else:
            documents = retriever.get_relevant_documents(request.query)
            results = [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 1.0 - doc.metadata.get("distance", 0)
                    if doc.metadata.get("distance") is not None
                    else None,
                }
                for doc in documents
            ]

        return [SearchResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/duplicates", response_model=dict)
async def find_duplicates():
    """Find duplicate documents based on file hash."""
    vector_service = VectorService()
    unique_docs = _get_unique_documents(vector_service)

    hash_groups = {}
    for doc_id, doc in unique_docs.items():
        if doc.file_hash:
            if doc.file_hash not in hash_groups:
                hash_groups[doc.file_hash] = []
            hash_groups[doc.file_hash].append(doc)

    duplicates = {
        file_hash: docs for file_hash, docs in hash_groups.items() if len(docs) > 1
    }

    result = {
        "total_duplicate_groups": len(duplicates),
        "duplicates": {
            file_hash: [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "created_at": doc.created_at,
                    "original_path": doc.original_path,
                    "storage_path": doc.storage_path,
                }
                for doc in docs
            ]
            for file_hash, docs in duplicates.items()
        },
    }

    return result

