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
    """Source type enumeration."""

    PDF = "pdf"
    URL = "url"
    NOTE = "note"
    MARKDOWN = "markdown"


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
    source: SourceType = Field(..., description="Document source type")
    chunk_index: int = Field(
        default=0, description="Chunk index if document is split into chunks"
    )
    chunk_total: Optional[int] = Field(
        None, description="Total number of chunks if document is split"
    )
    author: Optional[str] = Field(None, description="Document author")
    description: Optional[str] = Field(None, description="Document description")

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
        metadata = {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type.value,
            "title": self.title,
            "created_at": self.created_at,
            "source": self.source.value,
            "chunk_index": self.chunk_index,
        }

        if self.file_path:
            metadata["file_path"] = self.file_path
        if self.updated_at:
            metadata["updated_at"] = self.updated_at
        if self.tags:
            # Convert list to comma-separated string for ChromaDB
            metadata["tags"] = ",".join(self.tags)
        if self.chunk_total is not None:
            metadata["chunk_total"] = self.chunk_total
        if self.author:
            metadata["author"] = self.author
        if self.description:
            metadata["description"] = self.description

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

        return cls(
            doc_id=metadata["doc_id"],
            doc_type=DocType(metadata["doc_type"]),
            file_path=metadata.get("file_path"),
            title=metadata["title"],
            created_at=metadata["created_at"],
            updated_at=metadata.get("updated_at"),
            tags=tags,
            source=SourceType(metadata["source"]),
            chunk_index=metadata.get("chunk_index", 0),
            chunk_total=metadata.get("chunk_total"),
            author=metadata.get("author"),
            description=metadata.get("description"),
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

