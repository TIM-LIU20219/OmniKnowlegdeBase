"""Document chunking service for splitting documents into chunks."""

import logging
from typing import List

from backend.app.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Chunking strategies
class ChunkingStrategy:
    """Available chunking strategies."""
    CHARACTER_BASED = "character"  # Character-based with sentence boundary detection
    SENTENCE_BASED = "sentence"  # Sentence-based chunking
    PARAGRAPH_BASED = "paragraph"  # Paragraph-based chunking
    HYBRID = "hybrid"  # Hybrid: paragraph first, then sentence if needed


class ChunkingService:
    """Service for splitting documents into chunks for vectorization."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        strategy: str = ChunkingStrategy.HYBRID,
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            strategy: Chunking strategy ('character', 'sentence', 'paragraph', 'hybrid')
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        logger.info(
            f"Initialized chunking service: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, strategy={strategy}"
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks using the configured strategy.

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

        # Route to appropriate chunking method based on strategy
        if self.strategy == ChunkingStrategy.PARAGRAPH_BASED:
            chunks = self.chunk_by_paragraphs(text)
        elif self.strategy == ChunkingStrategy.SENTENCE_BASED:
            # Estimate sentences per chunk based on average sentence length
            avg_sentence_length = self.chunk_size // 50  # Rough estimate
            chunks = self.chunk_by_sentences(text, sentences_per_chunk=avg_sentence_length)
        elif self.strategy == ChunkingStrategy.HYBRID:
            chunks = self.chunk_hybrid(text)
        else:  # CHARACTER_BASED (default)
            chunks = self.chunk_by_characters(text)

        # Filter out reference sections
        filtered_chunks = []
        for chunk in chunks:
            if chunk and not TextCleaner.is_reference_section(chunk):
                filtered_chunks.append(chunk)
            elif chunk:
                logger.debug(f"Skipped reference section chunk: {chunk[:50]}...")

        logger.debug(f"Split text into {len(filtered_chunks)} chunks using {self.strategy} strategy")
        return filtered_chunks

    def chunk_by_characters(self, text: str) -> List[str]:
        """
        Split text into chunks with character-based splitting and sentence boundary detection.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
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

        return chunks

    def chunk_hybrid(self, text: str) -> List[str]:
        """
        Hybrid chunking strategy: paragraph-first, then sentence-based for large paragraphs.

        This strategy:
        1. First splits by paragraphs
        2. If a paragraph exceeds chunk_size, splits it by sentences
        3. Combines small paragraphs until reaching chunk_size

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            # Fallback to sentence-based if no paragraph breaks found
            return self.chunk_by_sentences(text)

        chunks = []
        current_chunk = []

        for paragraph in paragraphs:
            # If paragraph is too large, split it by sentences first
            if len(paragraph) > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []

                # Split large paragraph by sentences
                sentences = self._split_sentences(paragraph)
                sentence_chunks = []
                current_sentence_chunk = []

                for sentence in sentences:
                    potential_chunk = " ".join(current_sentence_chunk + [sentence])
                    if len(potential_chunk) <= self.chunk_size:
                        current_sentence_chunk.append(sentence)
                    else:
                        if current_sentence_chunk:
                            sentence_chunks.append(" ".join(current_sentence_chunk))
                        current_sentence_chunk = [sentence]

                if current_sentence_chunk:
                    sentence_chunks.append(" ".join(current_sentence_chunk))

                chunks.extend(sentence_chunks)
                continue

            # Check if adding this paragraph would exceed chunk size
            potential_chunk = "\n\n".join(current_chunk + [paragraph])

            if len(potential_chunk) <= self.chunk_size:
                current_chunk.append(paragraph)
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                # Start new chunk with this paragraph
                current_chunk = [paragraph]

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

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
        Supports both English and Chinese punctuation.

        Args:
            text: Text to search
            start: Start position
            end: End position

        Returns:
            Position of sentence boundary, or end if not found
        """
        # Look for sentence endings: English and Chinese punctuation
        # English: . ! ? followed by space or newline
        # Chinese: 。！？ followed by space, newline, or next character
        sentence_endings = [
            ". ", ".\n", "! ", "!\n", "? ", "?\n",  # English
            "。", "！", "？",  # Chinese (can be followed by anything)
            "。 ", "。\n", "！ ", "！\n", "？ ", "？\n",  # Chinese with space/newline
        ]

        for i in range(end - 1, start, -1):
            # Check two-character patterns (English with space/newline)
            if i + 1 < len(text):
                two_char = text[i : i + 2]
                if two_char in sentence_endings:
                    return i + 2

            # Check single-character patterns (Chinese punctuation)
            if i < len(text):
                char = text[i]
                # Chinese punctuation can end a sentence
                if char in ["。", "！", "？"]:
                    # Check if followed by space, newline, or end of text
                    if i + 1 >= len(text) or text[i + 1] in [" ", "\n", "\t"]:
                        return i + 1

        return end

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        Supports both English and Chinese punctuation.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Split by sentence endings (English and Chinese)
        # Pattern matches: . ! ? (English) or 。！？ (Chinese) followed by optional whitespace
        pattern = r"([.!?。！？]+[\s\n]*)"
        sentences = re.split(pattern, text)
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

