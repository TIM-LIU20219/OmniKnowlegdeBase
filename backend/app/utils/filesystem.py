"""File system utilities for managing directories and files."""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Base directories - relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
NOTES_DIR = BASE_DIR / "notes"
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [NOTES_DIR, DOCUMENTS_DIR, CHROMA_DB_DIR]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

    # Create .gitkeep files to ensure directories are tracked
    for directory in [NOTES_DIR, DOCUMENTS_DIR]:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            logger.debug(f"Created .gitkeep in {directory}")


def get_notes_directory() -> Path:
    """
    Get the notes directory path.

    Returns:
        Path to notes directory
    """
    return NOTES_DIR


def get_documents_directory() -> Path:
    """
    Get the documents directory path.

    Returns:
        Path to documents directory
    """
    return DOCUMENTS_DIR


def get_chroma_db_directory() -> Path:
    """
    Get the ChromaDB directory path.

    Returns:
        Path to ChromaDB directory
    """
    return CHROMA_DB_DIR


def list_note_files() -> List[Path]:
    """
    List all markdown note files.

    Returns:
        List of note file paths
    """
    notes = []
    if NOTES_DIR.exists():
        notes = list(NOTES_DIR.rglob("*.md"))
    logger.debug(f"Found {len(notes)} note files")
    return notes


def list_document_files() -> List[Path]:
    """
    List all document files.

    Returns:
        List of document file paths
    """
    documents = []
    if DOCUMENTS_DIR.exists():
        # Common document extensions
        extensions = ["*.pdf", "*.md", "*.txt"]
        for ext in extensions:
            documents.extend(list(DOCUMENTS_DIR.rglob(ext)))
    logger.debug(f"Found {len(documents)} document files")
    return documents

