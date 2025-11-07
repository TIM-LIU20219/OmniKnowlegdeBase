"""Agent tools for Agentic Search - defines search and retrieval tools."""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from backend.app.models.metadata import NoteMetadata
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.retriever import ChromaDBRetriever
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class AgentTools:
    """Collection of tools for agentic search."""

    def __init__(
        self,
        note_metadata_service: NoteMetadataService,
        note_file_service: NoteFileService,
        vector_service: VectorService,
        embedding_service: EmbeddingService,
        collection_name: str = "documents",
    ):
        """
        Initialize agent tools.

        Args:
            note_metadata_service: Service for note metadata queries
            note_file_service: Service for reading note files
            vector_service: Service for vector search
            embedding_service: Service for generating embeddings
            collection_name: ChromaDB collection name for document search
        """
        self.note_metadata_service = note_metadata_service
        self.note_file_service = note_file_service
        self.vector_service = vector_service
        self.embedding_service = embedding_service
        self.collection_name = collection_name

        # Create retriever for PDF/document chunks
        self.retriever = ChromaDBRetriever(
            vector_service=vector_service,
            embedding_service=embedding_service,
            collection_name=collection_name,
            k=5,
        )

        logger.info("Initialized AgentTools")

    def search_notes_by_title(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search notes by title using semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of note metadata dictionaries
        """
        try:
            # Get all notes
            all_notes = self.note_metadata_service.list_all_notes()

            if not all_notes:
                return []

            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)

            # Generate embeddings for all note titles
            note_titles = [note.title for note in all_notes]
            title_embeddings = self.embedding_service.embed_texts(note_titles)

            # Calculate cosine similarity
            try:
                import numpy as np
            except ImportError:
                logger.error("numpy is required for note title search. Install it with: pip install numpy")
                return []

            query_vec = np.array(query_embedding)
            similarities = []
            for title_emb in title_embeddings:
                title_vec = np.array(title_emb)
                # Cosine similarity
                norm_query = np.linalg.norm(query_vec)
                norm_title = np.linalg.norm(title_vec)
                if norm_query > 0 and norm_title > 0:
                    similarity = np.dot(query_vec, title_vec) / (norm_query * norm_title)
                else:
                    similarity = 0.0
                similarities.append(similarity)

            # Sort by similarity and get top results
            sorted_indices = sorted(
                range(len(similarities)), key=lambda i: similarities[i], reverse=True
            )
            top_indices = sorted_indices[:limit]

            results = []
            for idx in top_indices:
                note = all_notes[idx]
                results.append(
                    {
                        "note_id": note.note_id,
                        "title": note.title,
                        "file_path": note.file_path,
                        "tags": note.tags,
                        "links": note.links,
                        "similarity": float(similarities[idx]),
                    }
                )

            logger.debug(f"Found {len(results)} notes matching '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching notes by title: {e}")
            return []

    def get_note_metadata(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Get note metadata by note_id.

        Args:
            note_id: Note identifier

        Returns:
            Note metadata dictionary or None if not found
        """
        try:
            note = self.note_metadata_service.get_note_metadata(note_id)
            if not note:
                return None

            return {
                "note_id": note.note_id,
                "title": note.title,
                "file_path": note.file_path,
                "tags": note.tags,
                "links": note.links,
                "frontmatter": note.frontmatter,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting note metadata: {e}")
            return None

    def get_notes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all notes with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of note metadata dictionaries
        """
        try:
            notes = self.note_metadata_service.get_notes_by_tag(tag)
            return [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "file_path": note.file_path,
                    "tags": note.tags,
                    "links": note.links,
                }
                for note in notes
            ]

        except Exception as e:
            logger.error(f"Error getting notes by tag: {e}")
            return []

    def get_linked_notes(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Get all notes linked from a given note.

        Args:
            note_id: Source note identifier

        Returns:
            List of linked note metadata dictionaries
        """
        try:
            notes = self.note_metadata_service.get_linked_notes(note_id)
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
            logger.error(f"Error getting linked notes: {e}")
            return []

    def get_backlinks(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Get all notes that link to a given note (backlinks).

        Args:
            note_id: Target note identifier

        Returns:
            List of backlink note metadata dictionaries
        """
        try:
            notes = self.note_metadata_service.get_backlinks(note_id)
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
            logger.error(f"Error getting backlinks: {e}")
            return []

    def read_note_content(self, note_id: str) -> Optional[str]:
        """
        Read full content of a note.

        Args:
            note_id: Note identifier

        Returns:
            Note content as string or None if not found
        """
        try:
            note = self.note_metadata_service.get_note_metadata(note_id)
            if not note:
                return None

            _, _, content = self.note_file_service.read_note(note.file_path)
            return content

        except Exception as e:
            logger.error(f"Error reading note content: {e}")
            return None

    def search_pdf_chunks(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search PDF/document chunks using vector similarity.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of document chunk dictionaries
        """
        try:
            # Temporarily update retriever k
            original_k = self.retriever.k
            self.retriever.k = limit

            documents = self.retriever.get_relevant_documents(query)

            # Restore original k
            self.retriever.k = original_k

            results = []
            for doc in documents:
                results.append(
                    {
                        "text": doc.page_content,
                        "title": doc.metadata.get("title", "Unknown"),
                        "doc_id": doc.metadata.get("doc_id"),
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "distance": doc.metadata.get("distance"),
                        "source": doc.metadata.get("source", "unknown"),
                    }
                )

            logger.debug(f"Found {len(results)} document chunks matching '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching PDF chunks: {e}")
            return []

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function calling format tool definitions.

        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_notes_by_title",
                    "description": "Search notes by title using semantic similarity. Use this to find relevant notes when the user asks about a specific topic or concept.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant notes by title",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_note_metadata",
                    "description": "Get metadata (tags, links, frontmatter) for a specific note by its note_id. Use this after finding a relevant note to get more information about it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "string",
                                "description": "Note identifier (note_id)",
                            },
                        },
                        "required": ["note_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_notes_by_tag",
                    "description": "Get all notes with a specific tag. Use this when the user mentions a tag or wants to filter notes by category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tag": {
                                "type": "string",
                                "description": "Tag name to search for",
                            },
                        },
                        "required": ["tag"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_linked_notes",
                    "description": "Get all notes linked from a given note. Use this to explore related notes through Obsidian-style links.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "string",
                                "description": "Source note identifier",
                            },
                        },
                        "required": ["note_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_backlinks",
                    "description": "Get all notes that link to a given note (backlinks). Use this to find notes that reference a specific note.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "string",
                                "description": "Target note identifier",
                            },
                        },
                        "required": ["note_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_note_content",
                    "description": "Read the full content of a note. Use this to get the complete text of a note after finding it relevant.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "string",
                                "description": "Note identifier",
                            },
                        },
                        "required": ["note_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_pdf_chunks",
                    "description": "Search PDF documents and other document chunks using vector similarity. Use this as a fallback when notes don't contain the information, or when searching for information from PDF documents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for document chunks",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool by name with arguments.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool execution result
        """
        tool_map = {
            "search_notes_by_title": self.search_notes_by_title,
            "get_note_metadata": self.get_note_metadata,
            "get_notes_by_tag": self.get_notes_by_tag,
            "get_linked_notes": self.get_linked_notes,
            "get_backlinks": self.get_backlinks,
            "read_note_content": self.read_note_content,
            "search_pdf_chunks": self.search_pdf_chunks,
        }

        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")

        return tool_map[tool_name](**kwargs)

