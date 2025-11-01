"""Document chunking service for splitting documents into chunks."""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class ChunkingService:
    """Service for splitting documents into chunks for vectorization."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        logger.info(
            f"Initialized chunking service: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) == 0:
            return []

        # If text is shorter than chunk_size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Determine chunk end position
            end = start + self.chunk_size

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for sentence endings within last 20% of chunk
                search_start = max(start + int(self.chunk_size * 0.8), end - 100)
                sentence_end = self._find_sentence_boundary(text, search_start, end)

                if sentence_end > start:
                    end = sentence_end

            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start >= len(text):
                break

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def chunk_by_sentences(
        self, text: str, sentences_per_chunk: int = 10
    ) -> List[str]:
        """
        Split text into chunks based on sentences.

        Args:
            text: Text to chunk
            sentences_per_chunk: Number of sentences per chunk

        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) == 0:
            return []

        # Split into sentences
        sentences = self._split_sentences(text)

        if len(sentences) <= sentences_per_chunk:
            return [text]

        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk_sentences = sentences[i : i + sentences_per_chunk]
            chunk = " ".join(chunk_sentences).strip()
            if chunk:
                chunks.append(chunk)

        logger.debug(f"Split text into {len(chunks)} sentence-based chunks")
        return chunks

    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text into chunks based on paragraphs.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) == 0:
            return []

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            return [text]

        chunks = []
        current_chunk = []

        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed chunk size
            potential_chunk = "\n\n".join(current_chunk + [paragraph])

            if len(potential_chunk) <= self.chunk_size:
                current_chunk.append(paragraph)
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                # Start new chunk
                current_chunk = [paragraph]

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        logger.debug(f"Split text into {len(chunks)} paragraph-based chunks")
        return chunks

    def _find_sentence_boundary(
        self, text: str, start: int, end: int
    ) -> int:
        """
        Find sentence boundary within a range.

        Args:
            text: Text to search
            start: Start position
            end: End position

        Returns:
            Position of sentence boundary, or end if not found
        """
        # Look for sentence endings: . ! ? followed by space or newline
        sentence_endings = [". ", ".\n", "! ", "!\n", "? ", "?\n"]

        for i in range(end - 1, start, -1):
            if i + 1 < len(text):
                two_char = text[i : i + 2]
                if two_char in sentence_endings:
                    return i + 2

        return end

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Split by sentence endings followed by space or newline
        sentences = re.split(r"([.!?]+\s+)", text)
        result = []

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            sentence = sentence.strip()
            if sentence:
                result.append(sentence)

        # Handle last sentence if there's no ending punctuation
        if len(sentences) % 2 == 1:
            last = sentences[-1].strip()
            if last:
                result.append(last)

        return result

