"""Pydantic schemas for API requests and responses."""

from typing import List, Optional

from pydantic import BaseModel, Field

from backend.app.models.metadata import DocumentMetadata, NoteMetadata


# Document API Schemas
class DocumentCreateRequest(BaseModel):
    """Request schema for document creation."""

    url: Optional[str] = Field(None, description="URL to fetch and process")
    skip_duplicates: bool = Field(True, description="Skip duplicate documents")
    import_batch: Optional[str] = Field(None, description="Batch identifier")


class DocumentSearchRequest(BaseModel):
    """Request schema for document search."""

    query: str = Field(..., description="Search query")
    k: int = Field(5, description="Number of results to return")
    show_source_info: bool = Field(False, description="Include source file information")


class SearchResult(BaseModel):
    """Search result schema."""

    text: str = Field(..., description="Document chunk text")
    metadata: dict = Field(..., description="Document metadata")
    score: Optional[float] = Field(None, description="Similarity score")
    source_info: Optional[dict] = Field(None, description="Source file information")


class DocumentResponse(BaseModel):
    """Response schema for document."""

    doc_id: str
    title: str
    source: str
    created_at: str
    updated_at: Optional[str] = None
    chunk_total: Optional[int] = None
    tags: List[str] = []
    file_path: Optional[str] = None
    original_path: Optional[str] = None
    storage_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    file_mtime: Optional[str] = None
    import_batch: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_metadata(cls, metadata: DocumentMetadata) -> "DocumentResponse":
        """Create DocumentResponse from DocumentMetadata."""
        return cls(
            doc_id=metadata.doc_id,
            title=metadata.title,
            source=metadata.source.value if hasattr(metadata.source, "value") else str(metadata.source),
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            chunk_total=metadata.chunk_total,
            tags=metadata.tags,
            file_path=metadata.file_path,
            original_path=metadata.original_path,
            storage_path=metadata.storage_path,
            file_hash=metadata.file_hash,
            file_size=metadata.file_size,
            file_mtime=metadata.file_mtime,
            import_batch=metadata.import_batch,
            author=metadata.author,
            description=metadata.description,
        )


class DocumentListResponse(BaseModel):
    """Response schema for document list."""

    documents: List[DocumentResponse]
    total: int


class ChunkResponse(BaseModel):
    """Response schema for document chunk."""

    chunk_index: int
    chunk_total: int
    content: str
    metadata: dict


# RAG API Schemas
class RAGQueryRequest(BaseModel):
    """Request schema for RAG query."""

    question: str = Field(..., description="User question")
    collection: str = Field("documents", description="Collection name to query")
    k: int = Field(4, description="Number of documents to retrieve")
    threshold: Optional[float] = Field(None, description="Similarity score threshold (0-1)")


class RAGQueryResponse(BaseModel):
    """Response schema for RAG query."""

    answer: str = Field(..., description="Generated answer")
    sources: List[dict] = Field(..., description="Source documents")
    metadata: dict = Field(..., description="Query metadata")


class StreamChunk(BaseModel):
    """Stream chunk schema for SSE."""

    type: str = Field(..., description="Chunk type: chunk, tool_call, done")
    content: Optional[str] = Field(None, description="Text content for chunk type")
    data: Optional[dict] = Field(None, description="Data for tool_call or done type")


class AgenticQueryRequest(BaseModel):
    """Request schema for Agentic Search query."""

    question: str = Field(..., description="User question")
    strategy: str = Field("hybrid", description="Search strategy: note-first, hybrid")
    max_iterations: int = Field(5, description="Maximum tool calling iterations")


class AgenticQueryResponse(BaseModel):
    """Response schema for Agentic Search query."""

    answer: str = Field(..., description="Generated answer")
    sources: List[dict] = Field(..., description="Source documents")
    tool_calls: List[dict] = Field(..., description="Tool call history")
    metadata: dict = Field(..., description="Query metadata")


# Note API Schemas
class NoteCreateRequest(BaseModel):
    """Request schema for note creation."""

    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    file_path: Optional[str] = Field(None, description="File path (relative to notes directory)")
    tags: Optional[List[str]] = Field(None, description="Note tags")


class NoteUpdateRequest(BaseModel):
    """Request schema for note update."""

    content: Optional[str] = Field(None, description="New content")
    title: Optional[str] = Field(None, description="New title")
    tags: Optional[List[str]] = Field(None, description="New tags")


class NoteResponse(BaseModel):
    """Response schema for note."""

    title: str
    file_path: str
    frontmatter: dict
    content: str

    @classmethod
    def from_note(cls, title: str, file_path: str, frontmatter: dict, content: str) -> "NoteResponse":
        """Create NoteResponse from note data."""
        return cls(title=title, file_path=file_path, frontmatter=frontmatter, content=content)


class NoteSearchRequest(BaseModel):
    """Request schema for note search."""

    query: Optional[str] = Field(None, description="Semantic search query")
    tag: Optional[str] = Field(None, description="Filter by tag")
    limit: int = Field(10, description="Maximum number of results")


class NoteLinkResponse(BaseModel):
    """Response schema for note links."""

    note_id: str
    linked_notes: List[dict]
    backlinks: List[dict]


# Vector Store API Schemas
class VectorQueryRequest(BaseModel):
    """Request schema for vector query."""

    query_text: str = Field(..., description="Query text")
    k: int = Field(5, description="Number of results to return")


class VectorQueryResult(BaseModel):
    """Vector query result schema."""

    rank: int
    id: str
    content: str
    metadata: dict
    distance: Optional[float] = None
    similarity: Optional[float] = None


class CollectionStatsResponse(BaseModel):
    """Response schema for collection statistics."""

    collection: str
    total_documents: int
    unique_documents: Optional[int] = None


# System API Schemas
class SystemStatsResponse(BaseModel):
    """Response schema for system statistics."""

    total_documents: int
    total_notes: int
    total_vectors: int
    collections: List[dict]


# Note Generation API Schemas
class NoteGenerateRequest(BaseModel):
    """Request schema for note generation."""

    topic: str = Field(..., description="Topic or question for note generation")
    file_path: Optional[str] = Field(None, description="Optional file path for the note")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the note")
    style: Optional[str] = Field(None, description="Optional style instructions")


class NoteEnhanceRequest(BaseModel):
    """Request schema for note enhancement."""

    content: str = Field(..., description="Existing note content to enhance")
    file_path: Optional[str] = Field(None, description="Optional file path for the note")
    instruction: Optional[str] = Field(None, description="Enhancement instructions")


class NoteGenerationResponse(BaseModel):
    """Response schema for note generation."""

    mode: str = Field(..., description="Generation mode: /new or /ask")
    title: str = Field(..., description="Generated note title")
    content: str = Field(..., description="Generated note content")
    suggestions: str = Field(..., description="Similarity suggestions (as comments)")
    similar_notes: List[dict] = Field(default_factory=list, description="List of similar notes")
    added_links: List[str] = Field(default_factory=list, description="List of added links")
    sources: Optional[List[dict]] = Field(None, description="RAG retrieval sources (for /ask mode)")
    rag_context: Optional[str] = Field(None, description="RAG context summary (for /ask mode)")
    file_path: Optional[str] = Field(None, description="File path if provided")
    tags: Optional[List[str]] = Field(None, description="Tags if provided")
