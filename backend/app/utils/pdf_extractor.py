"""PDF extraction utilities with support for multiple backends.

This module provides a unified interface for PDF text extraction with
fallback support for multiple PDF libraries, prioritizing those with
better Chinese text support.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Unified PDF text extractor with multiple backend support."""

    def __init__(self, preferred_backend: Optional[str] = None):
        """
        Initialize PDF extractor.

        Args:
            preferred_backend: Preferred backend ('pymupdf', 'pdfplumber', 'pypdf')
                              If None, auto-selects best available backend
        """
        self.preferred_backend = preferred_backend
        self.available_backends = self._detect_available_backends()
        self.backend = self._select_backend()

    def _detect_available_backends(self) -> list:
        """Detect available PDF extraction backends."""
        backends = []

        # Check PyMuPDF (best for Chinese)
        try:
            import fitz  # noqa: F401
            backends.append("pymupdf")
        except ImportError:
            pass

        # Check pdfplumber (good for Chinese and tables)
        try:
            import pdfplumber  # noqa: F401
            backends.append("pdfplumber")
        except ImportError:
            pass

        # Check pypdf (fallback)
        try:
            from pypdf import PdfReader  # noqa: F401
            backends.append("pypdf")
        except ImportError:
            pass

        return backends

    def _select_backend(self) -> str:
        """Select the best available backend."""
        if self.preferred_backend and self.preferred_backend in self.available_backends:
            return self.preferred_backend

        # Priority order: pymupdf > pdfplumber > pypdf
        priority_order = ["pymupdf", "pdfplumber", "pypdf"]
        for backend in priority_order:
            if backend in self.available_backends:
                return backend

        raise RuntimeError(
            "No PDF extraction backend available. "
            "Please install one of: PyMuPDF, pdfplumber, or pypdf"
        )

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        logger.info(f"Extracting text from PDF using backend: {self.backend}")

        if self.backend == "pymupdf":
            return self._extract_with_pymupdf(pdf_path)
        elif self.backend == "pdfplumber":
            return self._extract_with_pdfplumber(pdf_path)
        elif self.backend == "pypdf":
            return self._extract_with_pypdf(pdf_path)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (best for Chinese)."""
        import fitz

        doc = fitz.open(str(pdf_path))
        text_parts = []

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Use 'text' mode for better text extraction
                # 'rawdict' mode provides more control but requires manual decoding
                page_text = page.get_text("text")
                if page_text:
                    text_parts.append(page_text)
        finally:
            doc.close()

        return "\n\n".join(text_parts)

    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (good for Chinese and tables)."""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def _extract_with_pypdf(self, pdf_path: Path) -> str:
        """Extract text using pypdf (fallback)."""
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def extract_with_fallback(self, pdf_path: Path) -> Tuple[str, str]:
        """
        Extract text with automatic fallback if primary backend fails.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, backend_used)
        """
        # Try primary backend
        try:
            text = self.extract_text(pdf_path)
            return text, self.backend
        except Exception as e:
            logger.warning(
                f"Primary backend {self.backend} failed: {e}. "
                "Trying fallback backends..."
            )

        # Try fallback backends
        fallback_order = ["pymupdf", "pdfplumber", "pypdf"]
        original_backend = self.backend
        
        for backend in fallback_order:
            if backend == self.backend:
                continue
            if backend not in self.available_backends:
                continue

            try:
                logger.info(f"Trying fallback backend: {backend}")
                self.backend = backend
                text = self.extract_text(pdf_path)
                return text, backend
            except Exception as e:
                logger.warning(f"Fallback backend {backend} failed: {e}")
                continue
            finally:
                self.backend = original_backend

        raise RuntimeError("All PDF extraction backends failed")


def extract_pdf_text(pdf_path: Path, backend: Optional[str] = None) -> str:
    """
    Convenience function to extract text from PDF.

    Args:
        pdf_path: Path to PDF file
        backend: Optional backend preference ('pymupdf', 'pdfplumber', 'pypdf')

    Returns:
        Extracted text
    """
    extractor = PDFExtractor(preferred_backend=backend)
    return extractor.extract_text(pdf_path)


def extract_pdf_text_with_fallback(pdf_path: Path) -> Tuple[str, str]:
    """
    Extract text with automatic fallback.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Tuple of (extracted_text, backend_used)
    """
    extractor = PDFExtractor()
    return extractor.extract_with_fallback(pdf_path)

