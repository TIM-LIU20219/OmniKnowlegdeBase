"""File system utilities for managing directories and files."""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Base directories - relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
NOTES_DIR = BASE_DIR / "notes"
RESOURCES_DIR = BASE_DIR / "resources"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [NOTES_DIR, RESOURCES_DIR, CHROMA_DB_DIR]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

    # Create .gitkeep files to ensure directories are tracked
    for directory in [NOTES_DIR, RESOURCES_DIR]:
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


def get_resources_directory() -> Path:
    """
    Get the resources directory path.

    Returns:
        Path to resources directory
    """
    return RESOURCES_DIR


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
    List all document files from resources directory.

    Returns:
        List of document file paths
    """
    documents = []
    if RESOURCES_DIR.exists():
        # Common document extensions
        extensions = ["*.pdf", "*.md", "*.txt", "*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.go", "*.rs", "*.rb", "*.php"]
        for ext in extensions:
            documents.extend(list(RESOURCES_DIR.rglob(ext)))
    logger.debug(f"Found {len(documents)} document files")
    return documents


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes
    """
    if not file_path.exists():
        return 0
    return file_path.stat().st_size


def get_file_info(file_path: Path) -> dict:
    """
    Get file information dictionary.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    if not file_path.exists():
        return {}

    stat = file_path.stat()
    return {
        "name": file_path.name,
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
    }


def create_subdirectory(base_dir: Path, subdir_name: str) -> Path:
    """
    Create a subdirectory if it doesn't exist.

    Args:
        base_dir: Base directory path
        subdir_name: Subdirectory name

    Returns:
        Path to created subdirectory
    """
    subdir = base_dir / subdir_name
    subdir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured subdirectory exists: {subdir}")
    return subdir


def sanitize_path(path_str: str) -> str:
    """
    Sanitize a path string by removing invalid characters.

    Args:
        path_str: Path string to sanitize

    Returns:
        Sanitized path string
    """
    # Remove invalid characters for Windows/Unix
    invalid_chars = r'<>:"/\|?*'
    sanitized = "".join(c if c not in invalid_chars else "_" for c in path_str)
    return sanitized.strip()


def ensure_file_directory(file_path: Path):
    """
    Ensure the parent directory of a file exists.

    Args:
        file_path: Path to file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured parent directory exists: {file_path.parent}")

