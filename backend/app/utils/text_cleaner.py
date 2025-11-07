"""Text cleaning utilities for document processing."""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class TextCleaner:
    """Utility class for cleaning extracted text from documents."""

    # Patterns for identifying special fields
    REFERENCE_PATTERNS = [
        r"^\[\d+\]\s+",  # [1] reference format
        r"^\d+\.\s+[A-Z][a-z]+.*\d{4}",  # Numbered reference format
        r"^[A-Z][a-z]+\s+et\s+al\.",  # Author et al. format
        r"arXiv:\s*\d{4}\.\d+",  # arXiv references
        r"ISBN:\s*\d+",  # ISBN references
        r"In:\s*[A-Z]+",  # Conference/journal references
    ]

    # Patterns for identifying figure/table captions
    FIGURE_PATTERNS = [
        r"^图\s*\d+[\.:：]",  # 图1. or 图1:
        r"^Figure\s*\d+[\.:]",  # Figure 1.
        r"^表\s*\d+[\.:：]",  # 表1. or 表1:
        r"^Table\s*\d+[\.:]",  # Table 1.
        r"^๭\d+",  # Special figure markers
    ]

    # Patterns for identifying page numbers and headers/footers
    PAGE_PATTERNS = [
        r"^\d+$",  # Standalone numbers (likely page numbers)
        r"^第\s*\d+\s*页",  # 第X页
        r"^Page\s+\d+",  # Page X
    ]

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text by removing common artifacts.
        Preserves paragraph structure (double newlines).

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Preserve paragraph breaks - only normalize spaces/tabs, keep newlines
        # Replace multiple spaces/tabs with single space (but preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)  # Only spaces and tabs, not newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Normalize paragraph breaks

        # Remove hyphenation artifacts (word-\nword -> word word)
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

        # Remove excessive punctuation
        text = re.sub(r"\.{3,}", "...", text)

        # Normalize Chinese punctuation spacing
        text = re.sub(r"\s+([，。！？；：])", r"\1", text)
        text = re.sub(r"([，。！？；：])\s+", r"\1 ", text)

        return text.strip()

    @staticmethod
    def remove_special_fields(text: str) -> str:
        """
        Remove special fields like references, figure captions, etc.
        More conservative approach - only remove clearly identifiable special fields.

        Args:
            text: Text to clean

        Returns:
            Text with special fields removed
        """
        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            original_line = line
            line = line.strip()
            
            # Preserve empty lines for paragraph structure
            if not line:
                cleaned_lines.append("")
                continue

            # Check if line matches reference patterns (strict matching)
            is_reference = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in TextCleaner.REFERENCE_PATTERNS
            )

            # Check if line matches figure/table patterns
            is_figure = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in TextCleaner.FIGURE_PATTERNS
            )

            # More conservative page number detection
            # Only match if it's clearly a page number (very short, standalone)
            is_page = False
            if len(line) <= 3:  # Only very short lines (likely page numbers)
                is_page = any(
                    re.match(pattern, line, re.IGNORECASE)
                    for pattern in [
                        r"^\d+$",  # Standalone numbers (1-999)
                        r"^第\s*\d+\s*页",  # 第X页
                        r"^Page\s+\d+",  # Page X
                    ]
                )
            # Don't filter longer lines that might contain numbers but are actual content

            # Skip only clearly identifiable special fields
            if not (is_reference or is_figure or is_page):
                cleaned_lines.append(original_line)  # Preserve original formatting
            else:
                logger.debug(f"Filtered special field: {line[:50]}...")

        return "\n".join(cleaned_lines)

    @staticmethod
    def remove_garbled_text(text: str, threshold: float = 0.2) -> str:
        """
        Remove lines with high proportion of non-printable or garbled characters.
        More lenient threshold to avoid removing valid content.

        Args:
            text: Text to clean
            threshold: Proportion threshold (0.0-1.0) for considering line garbled
                      Lower threshold = more lenient (default: 0.2)

        Returns:
            Text with garbled lines removed
        """
        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            if not line.strip():
                cleaned_lines.append(line)
                continue

            # Count printable ASCII and common Unicode characters
            printable_count = sum(
                1
                for char in line
                if char.isprintable()
                and (
                    ord(char) < 128  # ASCII
                    or "\u4e00" <= char <= "\u9fff"  # Chinese characters
                    or "\u3040" <= char <= "\u309f"  # Hiragana
                    or "\u30a0" <= char <= "\u30ff"  # Katakana
                    or "\uac00" <= char <= "\ud7a3"  # Hangul
                )
            )

            # Calculate proportion of printable characters
            if len(line) > 0:
                printable_ratio = printable_count / len(line)
                if printable_ratio >= threshold:
                    cleaned_lines.append(line)
                else:
                    logger.debug(f"Removed garbled line (ratio={printable_ratio:.2f}): {line[:50]}...")

        return "\n".join(cleaned_lines)

    @staticmethod
    def clean_pdf_text(text: str) -> str:
        """
        Comprehensive cleaning for PDF-extracted text.
        Preserves paragraph structure and uses conservative filtering.

        Args:
            text: Raw PDF-extracted text

        Returns:
            Cleaned text ready for chunking
        """
        if not text:
            return ""

        # Step 1: Basic cleaning (preserves paragraph structure)
        text = TextCleaner.clean_text(text)

        # Step 2: Remove garbled text (with more lenient threshold)
        # Lower threshold (0.2) to avoid removing valid content
        text = TextCleaner.remove_garbled_text(text, threshold=0.2)

        # Step 3: Remove special fields (conservative approach)
        # Only removes clearly identifiable references, figures, and page numbers
        text = TextCleaner.remove_special_fields(text)

        # Final cleanup - normalize paragraph breaks
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = text.strip()

        return text

    @staticmethod
    def is_reference_section(text: str) -> bool:
        """
        Check if a text chunk is primarily a reference section.

        Args:
            text: Text to check

        Returns:
            True if text appears to be a reference section
        """
        if not text:
            return False

        lines = text.split("\n")
        reference_line_count = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line matches reference patterns
            is_reference = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in TextCleaner.REFERENCE_PATTERNS
            )

            if is_reference:
                reference_line_count += 1

        # If more than 30% of lines are references, consider it a reference section
        if len(lines) > 0:
            return reference_line_count / len(lines) > 0.3

        return False

    @staticmethod
    def clean_for_embedding(content: str) -> str:
        """
        Clean markdown content for embedding generation.
        
        Removes structured markdown syntax while preserving text content:
        - Removes Obsidian-style links [[note-name]] but keeps the link text
        - Removes markdown tags (#tag) but keeps the tag text
        - Removes frontmatter (YAML between ---)
        - Preserves markdown headers (# Title) as they are part of content structure
        - Removes other markdown formatting but keeps text
        
        Args:
            content: Markdown content with structured elements
            
        Returns:
            Cleaned text suitable for embedding
        """
        if not content:
            return ""
        
        # Step 1: Remove frontmatter (YAML between ---)
        frontmatter_pattern = r"^---\s*\n.*?\n---\s*\n"
        content = re.sub(frontmatter_pattern, "", content, flags=re.DOTALL | re.MULTILINE)
        
        # Step 2: Replace Obsidian-style links [[note-name]] with just the note name
        # This preserves the semantic meaning while removing the link syntax
        obsidian_link_pattern = r"\[\[([^\]]+)\]\]"
        content = re.sub(obsidian_link_pattern, r"\1", content)
        
        # Step 3: Remove markdown tags (#tag) but keep the tag text
        # Match #tag at start of line or after whitespace, but not in headers
        tag_pattern = r"(?<!#)(?<!\w)#(\w+)"
        content = re.sub(tag_pattern, r"\1", content)
        
        # Step 4: Remove markdown link syntax [text](url) but keep the text
        markdown_link_pattern = r"\[([^\]]+)\]\([^\)]+\)"
        content = re.sub(markdown_link_pattern, r"\1", content)
        
        # Step 5: Remove image syntax ![alt](url) but keep alt text
        image_pattern = r"!\[([^\]]*)\]\([^\)]+\)"
        content = re.sub(image_pattern, r"\1", content)
        
        # Step 6: Remove inline code formatting but keep the code text
        inline_code_pattern = r"`([^`]+)`"
        content = re.sub(inline_code_pattern, r"\1", content)
        
        # Step 7: Remove bold/italic formatting but keep text
        # Remove **bold** and *italic*
        content = re.sub(r"\*\*([^\*]+)\*\*", r"\1", content)
        content = re.sub(r"\*([^\*]+)\*", r"\1", content)
        content = re.sub(r"__([^_]+)__", r"\1", content)
        content = re.sub(r"_([^_]+)_", r"\1", content)
        
        # Step 8: Remove strikethrough
        content = re.sub(r"~~([^~]+)~~", r"\1", content)
        
        # Step 9: Remove reference-style links [text][ref] but keep text
        ref_link_pattern = r"\[([^\]]+)\]\[[^\]]+\]"
        content = re.sub(ref_link_pattern, r"\1", content)
        
        # Step 10: Clean up extra whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)  # Normalize multiple newlines
        content = re.sub(r"[ \t]+", " ", content)  # Normalize spaces
        
        return content.strip()

