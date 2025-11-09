"""Pydantic models for document and note metadata."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Document type enumeration."""

    DOCUMENT = "document"
    NOTE = "note"


class SourceType(str, Enum):
    """Source type enumeration for all material types."""

    # Document types
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    
    # Web content
    URL = "url"
    WEBPAGE = "webpage"
    
    # Media types
    PICTURE = "picture"
    IMAGE = "image"  # Alias for picture
    VIDEO = "video"
    AUDIO = "audio"
    
    # Code
    CODE = "code"
    
    # Notes
    NOTE = "note"
    
    # Other
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata model for documents stored in ChromaDB."""

    doc_id: str = Field(..., description="Unique document identifier")
    doc_type: DocType = Field(..., description="Type of document (document or note)")
    file_path: Optional[str] = Field(None, description="File system path to the document")
    title: str = Field(..., description="Document title")
    created_at: str = Field(
        ..., description="ISO format creation timestamp"
    )
    updated_at: Optional[str] = Field(
        None, description="ISO format update timestamp"
    )
    tags: List[str] = Field(default_factory=list, description="Document tags")
    source: SourceType = Field(..., description="Document source type (pdf, url, picture, etc.)")
    
    # Links (for notes and documents that reference other materials)
    links: List[str] = Field(
        default_factory=list,
        description="List of linked note/material IDs or names"
    )
    
    chunk_index: int = Field(
        default=0, description="Chunk index if document is split into chunks"
    )
    chunk_total: Optional[int] = Field(
        None, description="Total number of chunks if document is split"
    )
    author: Optional[str] = Field(None, description="Document author")
    description: Optional[str] = Field(None, description="Document description")
    original_path: Optional[str] = Field(
        None,
        description="Original file path in resources folder (relative to project root)",
    )
    file_hash: Optional[str] = Field(
        None, description="SHA256 hash of file content for deduplication"
    )
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_mtime: Optional[str] = Field(
        None, description="File modification time (ISO format)"
    )
    storage_path: Optional[str] = Field(
        None,
        description="Path where file is stored (documents folder or original location)",
    )
    import_batch: Optional[str] = Field(
        None, description="Batch identifier for tracking import groups"
    )
    
    # Media-specific metadata
    mime_type: Optional[str] = Field(None, description="MIME type for media files (e.g., image/png)")
    width: Optional[int] = Field(None, description="Width in pixels (for images/videos)")
    height: Optional[int] = Field(None, description="Height in pixels (for images/videos)")
    duration: Optional[float] = Field(None, description="Duration in seconds (for audio/video)")

    class Config:
        """Pydantic config."""

        use_enum_values = True

    def to_chromadb_metadata(self) -> dict:
        """
        Convert to ChromaDB-compatible metadata format.

        ChromaDB metadata must be strings, numbers, or booleans.

        Returns:
            Dictionary suitable for ChromaDB metadata
        """
        # Handle doc_type - it may be Enum or string due to use_enum_values
        doc_type_value = self.doc_type.value if hasattr(self.doc_type, 'value') else str(self.doc_type)
        
        # Handle source - it may be Enum or string due to use_enum_values
        source_value = self.source.value if hasattr(self.source, 'value') else str(self.source)
        
        metadata = {
            "doc_id": self.doc_id,
            "doc_type": doc_type_value,
            "title": self.title,
            "created_at": self.created_at,
            "source": source_value,
            "chunk_index": self.chunk_index,
        }

        if self.file_path:
            metadata["file_path"] = self.file_path
        if self.updated_at:
            metadata["updated_at"] = self.updated_at
        if self.tags:
            # Convert list to comma-separated string for ChromaDB
            metadata["tags"] = ",".join(self.tags)
        if self.links:
            # Convert links list to comma-separated string
            metadata["links"] = ",".join(self.links)
        if self.chunk_total is not None:
            metadata["chunk_total"] = self.chunk_total
        if self.author:
            metadata["author"] = self.author
        if self.description:
            metadata["description"] = self.description
        if self.original_path:
            metadata["original_path"] = self.original_path
        if self.file_hash:
            metadata["file_hash"] = self.file_hash
        if self.file_size is not None:
            metadata["file_size"] = self.file_size
        if self.file_mtime:
            metadata["file_mtime"] = self.file_mtime
        if self.storage_path:
            metadata["storage_path"] = self.storage_path
        if self.import_batch:
            metadata["import_batch"] = self.import_batch
        
        # Media-specific metadata
        if self.mime_type:
            metadata["mime_type"] = self.mime_type
        if self.width is not None:
            metadata["width"] = self.width
        if self.height is not None:
            metadata["height"] = self.height
        if self.duration is not None:
            metadata["duration"] = self.duration

        return metadata

    @classmethod
    def from_chromadb_metadata(cls, metadata: dict) -> "DocumentMetadata":
        """
        Create DocumentMetadata from ChromaDB metadata.

        Args:
            metadata: ChromaDB metadata dictionary

        Returns:
            DocumentMetadata instance
        """
        # Parse tags from comma-separated string
        tags = []
        if "tags" in metadata and metadata["tags"]:
            tags = metadata["tags"].split(",") if isinstance(metadata["tags"], str) else metadata["tags"]
        
        # Parse links from comma-separated string
        links = []
        if "links" in metadata and metadata["links"]:
            links = metadata["links"].split(",") if isinstance(metadata["links"], str) else metadata["links"]

        return cls(
            doc_id=metadata["doc_id"],
            doc_type=DocType(metadata["doc_type"]),
            file_path=metadata.get("file_path"),
            title=metadata["title"],
            created_at=metadata["created_at"],
            updated_at=metadata.get("updated_at"),
            tags=tags,
            links=links,
            source=SourceType(metadata.get("source", "unknown")),
            chunk_index=metadata.get("chunk_index", 0),
            chunk_total=metadata.get("chunk_total"),
            author=metadata.get("author"),
            description=metadata.get("description"),
            original_path=metadata.get("original_path"),
            file_hash=metadata.get("file_hash"),
            file_size=metadata.get("file_size"),
            file_mtime=metadata.get("file_mtime"),
            storage_path=metadata.get("storage_path"),
            import_batch=metadata.get("import_batch"),
            mime_type=metadata.get("mime_type"),
            width=metadata.get("width"),
            height=metadata.get("height"),
            duration=metadata.get("duration"),
        )


class NoteMetadata(BaseModel):
    """Metadata model for Obsidian-style notes."""

    note_id: str = Field(..., description="Unique note identifier")
    title: str = Field(..., description="Note title")
    file_path: str = Field(..., description="Path to note file relative to notes directory")
    created_at: datetime = Field(..., description="Note creation timestamp")
    updated_at: datetime = Field(..., description="Note last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Note tags")
    links: List[str] = Field(
        default_factory=list, description="List of linked note names ([[note-name]])"
    )
    frontmatter: dict = Field(
        default_factory=dict, description="YAML frontmatter content"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}

