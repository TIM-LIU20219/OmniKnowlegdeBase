"""Note management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from backend.app.api.schemas import (
    NoteCreateRequest,
    NoteEnhanceRequest,
    NoteGenerateRequest,
    NoteGenerationResponse,
    NoteLinkResponse,
    NoteResponse,
    NoteSearchRequest,
    NoteUpdateRequest,
)
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.note_vectorization_service import NoteVectorizationService
from backend.app.services.workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(request: NoteCreateRequest):
    """Create a new note."""
    note_service = NoteFileService()

    try:
        note_path = note_service.create_note(
            title=request.title,
            content=request.content,
            file_path=request.file_path,
            tags=request.tags,
        )

        title, frontmatter, content = note_service.read_note(note_path)
        return NoteResponse.from_note(title, note_path, frontmatter, content)
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[str])
async def list_notes(subdirectory: Optional[str] = None):
    """List all notes."""
    note_service = NoteFileService()

    try:
        notes = note_service.list_notes(subdirectory=subdirectory)
        return [str(note) for note in notes]
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_path:path}", response_model=NoteResponse)
async def get_note(file_path: str):
    """Get note content."""
    note_service = NoteFileService()

    try:
        title, frontmatter, content = note_service.read_note(file_path)
        return NoteResponse.from_note(title, file_path, frontmatter, content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Note '{file_path}' not found")
    except Exception as e:
        logger.error(f"Error getting note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{file_path:path}", response_model=NoteResponse)
async def update_note(file_path: str, request: NoteUpdateRequest):
    """Update a note."""
    note_service = NoteFileService()

    try:
        note_path = note_service.update_note(
            file_path=file_path,
            content=request.content,
            title=request.title,
            tags=request.tags,
        )

        title, frontmatter, content = note_service.read_note(note_path)
        return NoteResponse.from_note(title, note_path, frontmatter, content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Note '{file_path}' not found")
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_path:path}", status_code=204)
async def delete_note(file_path: str):
    """Delete a note."""
    note_service = NoteFileService()

    try:
        deleted = note_service.delete_note(file_path)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Note '{file_path}' not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_path:path}/links", response_model=dict)
async def get_note_links(file_path: str):
    """Get links from a note."""
    note_service = NoteFileService()
    note_metadata_service = NoteMetadataService()

    try:
        metadata = note_service.get_note_metadata(file_path)
        links = metadata.links

        # Get linked notes from SQLite
        note_id = str(file_path).replace("\\", "/").replace(".md", "")
        linked_notes = note_metadata_service.get_linked_notes(note_id)
        backlinks = note_metadata_service.get_backlinks(note_id)

        return {
            "file_path": file_path,
            "links": links,
            "linked_notes": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "file_path": note.file_path,
                }
                for note in linked_notes
            ],
            "backlinks": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "file_path": note.file_path,
                }
                for note in backlinks
            ],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Note '{file_path}' not found")
    except Exception as e:
        logger.error(f"Error getting note links: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_path:path}/vectorize", response_model=dict)
async def vectorize_note(file_path: str, force: bool = False):
    """Vectorize a note."""
    vectorization_service = NoteVectorizationService()

    try:
        metadata = vectorization_service.vectorize_note(file_path, force=force)
        return {
            "doc_id": metadata.doc_id,
            "title": metadata.title,
            "chunks": metadata.chunk_total or 0,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Note '{file_path}' not found")
    except Exception as e:
        logger.error(f"Error vectorizing note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectorize/all", response_model=dict)
async def vectorize_all_notes(force: bool = False, incremental: bool = True):
    """Vectorize all notes."""
    vectorization_service = NoteVectorizationService()

    try:
        vectorized_count, skipped_count = vectorization_service.vectorize_all_notes(
            force=force, incremental=incremental
        )
        return {
            "vectorized": vectorized_count,
            "skipped": skipped_count,
        }
    except Exception as e:
        logger.error(f"Error vectorizing all notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[dict])
async def search_notes(request: NoteSearchRequest):
    """Search notes by semantic similarity or filter by tag."""
    vectorization_service = NoteVectorizationService()

    if not request.query and not request.tag:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'query' or 'tag' must be provided"
        )

    try:
        results = vectorization_service.search_notes(
            query=request.query, limit=request.limit, tag=request.tag
        )
        return results
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-tag/{tag}", response_model=List[dict])
async def get_notes_by_tag(tag: str):
    """Get notes by tag."""
    note_metadata_service = NoteMetadataService()

    try:
        notes = note_metadata_service.get_notes_by_tag(tag)
        return [
            {
                "note_id": note.note_id,
                "title": note.title,
                "file_path": note.file_path,
                "tags": note.tags,
            }
            for note in notes
        ]
    except Exception as e:
        logger.error(f"Error getting notes by tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}/linked", response_model=List[dict])
async def get_linked_notes(note_id: str):
    """Get linked notes."""
    note_metadata_service = NoteMetadataService()

    try:
        notes = note_metadata_service.get_linked_notes(note_id)
        return [
            {
                "note_id": note.note_id,
                "title": note.title,
                "file_path": note.file_path,
            }
            for note in notes
        ]
    except Exception as e:
        logger.error(f"Error getting linked notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}/backlinks", response_model=List[dict])
async def get_backlinks(note_id: str):
    """Get backlinks."""
    note_metadata_service = NoteMetadataService()

    try:
        notes = note_metadata_service.get_backlinks(note_id)
        return [
            {
                "note_id": note.note_id,
                "title": note.title,
                "file_path": note.file_path,
            }
            for note in notes
        ]
    except Exception as e:
        logger.error(f"Error getting backlinks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=NoteGenerationResponse)
async def generate_note(request: NoteGenerateRequest):
    """
    Generate a note using LLM.
    
    Supports two modes via topic prefix:
    - /new <topic>: Generate using LLM's own knowledge
    - /ask <question>: Generate using RAG retrieval first
    """
    orchestrator = WorkflowOrchestrator()

    try:
        # Build query with mode prefix if not present
        query = request.topic
        if not query.startswith(("/new", "/ask")):
            # Default to /ask mode if no prefix
            query = f"/ask {query}"

        result = orchestrator.execute(
            query=query,
            file_path=request.file_path,
            tags=request.tags,
            style=request.style,
        )

        return NoteGenerationResponse(**result)
    except Exception as e:
        logger.error(f"Error generating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance", response_model=NoteGenerationResponse)
async def enhance_note(request: NoteEnhanceRequest):
    """
    Enhance an existing note.
    
    Note: /enhance mode is not yet fully implemented.
    """
    orchestrator = WorkflowOrchestrator()

    try:
        query = f"/enhance {request.content}"
        result = orchestrator.execute(
            query=query,
            file_path=request.file_path,
            instruction=request.instruction,
        )

        return NoteGenerationResponse(**result)
    except Exception as e:
        logger.error(f"Error enhancing note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-and-save", response_model=NoteResponse)
async def generate_and_save_note(request: NoteGenerateRequest):
    """
    Generate a note and save it immediately.
    
    This endpoint generates a note and saves it to the file system.
    """
    orchestrator = WorkflowOrchestrator()
    note_service = NoteFileService()

    try:
        # Build query with mode prefix if not present
        query = request.topic
        if not query.startswith(("/new", "/ask")):
            query = f"/ask {query}"

        # Generate note
        result = orchestrator.execute(
            query=query,
            file_path=request.file_path,
            tags=request.tags,
            style=request.style,
        )

        # Combine content and suggestions
        full_content = result["content"]
        if result.get("suggestions"):
            full_content = f"{result['suggestions']}\n\n{full_content}"

        # Save note
        file_path = result.get("file_path") or request.file_path
        if not file_path:
            # Generate file path from title
            title = result["title"]
            safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
            file_path = f"{safe_title.replace(' ', '_')}.md"

        note_path = note_service.create_note(
            title=result["title"],
            content=full_content,
            file_path=file_path,
            tags=result.get("tags") or request.tags,
        )

        # Read back the note
        title, frontmatter, content = note_service.read_note(note_path)
        return NoteResponse.from_note(title, note_path, frontmatter, content)

    except Exception as e:
        logger.error(f"Error generating and saving note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

