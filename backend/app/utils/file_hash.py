"""File hash utilities for deduplication and file management."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of file content.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)

    Returns:
        Hexadecimal hash string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        raise

    hash_value = hash_obj.hexdigest()
    logger.debug(f"Calculated {algorithm} hash for '{file_path}': {hash_value[:8]}...")
    return hash_value


def get_file_metadata(file_path: Path) -> Dict[str, any]:
    """
    Get file metadata including size and modification time.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file metadata:
        - file_size: File size in bytes
        - file_mtime: File modification time (ISO format)

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = file_path.stat()
    return {
        "file_size": stat.st_size,
        "file_mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def get_file_hash_and_metadata(file_path: Path) -> Dict[str, any]:
    """
    Get both file hash and metadata in one call.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with:
        - file_hash: SHA256 hash of file content
        - file_size: File size in bytes
        - file_mtime: File modification time (ISO format)
    """
    return {
        "file_hash": calculate_file_hash(file_path),
        **get_file_metadata(file_path),
    }

