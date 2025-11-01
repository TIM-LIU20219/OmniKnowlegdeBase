"""
Standalone test script for backend document processing services.

This script allows testing backend services without Streamlit frontend.
It includes mock file generators and tests the complete processing pipeline.

Usage:
    python backend/test_document_processing.py
    # OR from project root:
    python -m backend.test_document_processing
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Add project root to Python path
# This allows imports to work when running as a script
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Print immediate feedback
print("=" * 60)
print("Backend Document Processing Test Suite")
print("=" * 60)
print("\nInitializing...")

from backend.app.services.document_service import DocumentService
from backend.app.utils.device_utils import get_device_info
from backend.app.utils.filesystem import DOCUMENTS_DIR, ensure_directories, ensure_file_directory
from backend.app.utils.logging_config import setup_logging

# Setup logging
setup_logging(log_level="INFO")


def create_mock_pdf(file_path: Path) -> Path:
    """
    Create a mock PDF file for testing.

    Args:
        file_path: Path where to create the PDF

    Returns:
        Path to created PDF file
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        # Create PDF with sample content
        c = canvas.Canvas(str(file_path), pagesize=letter)
        c.setFont("Helvetica", 16)
        c.drawString(100, 750, "Test Document")
        c.setFont("Helvetica", 12)
        
        # Add multiple pages of content
        content = """
        This is a test document for the OmniKnowledgeBase system.
        
        The document processing pipeline includes:
        1. Document parsing (PDF, Markdown, URL)
        2. Text extraction and cleaning
        3. Metadata extraction
        4. Text chunking with overlap
        5. Embedding generation
        6. Vector storage in ChromaDB
        
        This is a sample paragraph that will be chunked along with other content.
        The chunking service splits text into manageable pieces for vectorization.
        Each chunk is then embedded and stored in the vector database.
        
        The embedding service uses SentenceTransformer models to generate
        semantic representations of text. These embeddings enable semantic search
        and retrieval-augmented generation (RAG) capabilities.
        
        Another paragraph discussing document management features.
        The system supports multiple document types and sources.
        Files can be uploaded as PDFs, pasted as Markdown, or fetched from URLs.
        """
        
        y = 700
        for line in content.split("\n"):
            if line.strip():
                c.drawString(100, y, line.strip())
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 750
        
        c.save()
        logging.info(f"Created mock PDF: {file_path}")
        return file_path
        
    except ImportError:
        logging.warning("reportlab not installed. Skipping PDF test - install reportlab for PDF testing.")
        # Return None to skip PDF test instead of creating invalid file
        raise ImportError(
            "reportlab is required for PDF testing. Install it with: pip install reportlab\n"
            "Or skip PDF testing and test Markdown/URL processing instead."
        )


def create_mock_markdown() -> str:
    """
    Create mock Markdown content for testing.

    Returns:
        Markdown content string
    """
    return """---
title: Test Markdown Document
author: Test Author
tags: [test, markdown, sample]
description: A sample markdown document for testing
---

# Test Markdown Document

This is a **test document** created for testing the document processing pipeline.

## Features

The system supports:
- Markdown parsing
- Frontmatter extraction
- Link extraction
- Tag extraction

## Content

This is a sample paragraph with multiple sentences. The chunking service will split this into chunks. Each chunk will be embedded and stored in the vector database.

Another paragraph discussing the embedding process. The SentenceTransformer model generates semantic embeddings for each chunk.

### Links

Check out [OpenAI](https://openai.com) and internal links like [[another-note]].

Tags: #test #markdown #processing
"""


def test_pdf_processing(document_service: DocumentService, pdf_path: Optional[Path] = None):
    """
    Test PDF processing pipeline.

    Args:
        document_service: DocumentService instance
        pdf_path: Optional path to PDF file. If None, creates a mock PDF.
    """
    print("\n" + "="*60)
    print("Testing PDF Processing")
    print("="*60)
    
    if pdf_path is None:
        # Create temporary PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = Path(tmp_file.name)
        pdf_path = create_mock_pdf(tmp_path)
    
    try:
        print(f"\nProcessing PDF: {pdf_path}")
        metadata = document_service.process_and_store_pdf(pdf_path)
        
        print("\n✅ PDF Processing Successful!")
        print(f"   Document ID: {metadata.doc_id}")
        print(f"   Title: {metadata.title}")
        print(f"   Source: {metadata.source}")
        print(f"   Chunks created: {metadata.chunk_total}")
        print(f"   Created at: {metadata.created_at}")
        
        if metadata.author:
            print(f"   Author: {metadata.author}")
        
        if metadata.tags:
            print(f"   Tags: {', '.join(metadata.tags)}")
        
        return metadata
        
    except Exception as e:
        print(f"\n❌ Error processing PDF: {e}")
        logging.exception("PDF processing failed")
        raise
    finally:
        # Clean up temporary file if we created it
        if pdf_path.exists() and "tmp" in str(pdf_path):
            try:
                pdf_path.unlink()
            except Exception:
                pass


def test_markdown_processing(document_service: DocumentService, content: Optional[str] = None):
    """
    Test Markdown processing pipeline.

    Args:
        document_service: DocumentService instance
        content: Optional Markdown content. If None, uses mock content.
    """
    print("\n" + "="*60)
    print("Testing Markdown Processing")
    print("="*60)
    
    if content is None:
        content = create_mock_markdown()
    
    try:
        print(f"\nProcessing Markdown content ({len(content)} chars)...")
        metadata = document_service.process_and_store_markdown(content)
        
        # Save markdown content to file for reference
        saved_path = None
        if metadata.doc_id:
            # Sanitize title for filename
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in metadata.title)
            safe_title = safe_title[:50].strip()  # Limit length
            filename = f"{metadata.doc_id[:8]}_{safe_title}.md"
            saved_path = DOCUMENTS_DIR / filename
            ensure_file_directory(saved_path)
            saved_path.write_text(content, encoding='utf-8')
            print(f"   Saved to: {saved_path}")
        
        print("\n✅ Markdown Processing Successful!")
        print(f"   Document ID: {metadata.doc_id}")
        print(f"   Title: {metadata.title}")
        print(f"   Source: {metadata.source}")
        print(f"   Chunks created: {metadata.chunk_total}")
        print(f"   Created at: {metadata.created_at}")
        
        if metadata.author:
            print(f"   Author: {metadata.author}")
        
        if metadata.tags:
            print(f"   Tags: {', '.join(metadata.tags)}")
        
        if metadata.description:
            print(f"   Description: {metadata.description}")
        
        # Show content preview
        print(f"\n   Content preview (first 200 chars):")
        print(f"   {content[:200]}...")
        
        return metadata
        
    except Exception as e:
        print(f"\n❌ Error processing Markdown: {e}")
        logging.exception("Markdown processing failed")
        raise


def test_url_processing(document_service: DocumentService, url: str = "https://www.example.com"):
    """
    Test URL processing pipeline.

    Args:
        document_service: DocumentService instance
        url: URL to fetch and process
    """
    print("\n" + "="*60)
    print("Testing URL Processing")
    print("="*60)
    
    try:
        print(f"\nFetching and processing URL: {url}")
        # Process and store URL (this will fetch the URL content)
        metadata = document_service.process_and_store_url(url)
        
        # Get processed text separately for saving (will fetch URL again, but acceptable for testing)
        from backend.app.services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        processed_text, _ = processor.process_url(url)
        
        # Save URL content to file for reference
        saved_path = None
        if metadata.doc_id:
            # Sanitize title for filename
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in metadata.title)
            safe_title = safe_title[:50].strip()  # Limit length
            filename = f"{metadata.doc_id[:8]}_{safe_title}.txt"
            saved_path = DOCUMENTS_DIR / filename
            ensure_file_directory(saved_path)
            
            # Write content with metadata header
            content_to_save = f"""# URL Content: {metadata.title}
Source URL: {url}
Document ID: {metadata.doc_id}
Created: {metadata.created_at}
{'Description: ' + metadata.description if metadata.description else ''}
{'Tags: ' + ', '.join(metadata.tags) if metadata.tags else ''}

{'='*60}
Content:
{'='*60}

{processed_text}
"""
            saved_path.write_text(content_to_save, encoding='utf-8')
            print(f"   Saved to: {saved_path}")
        
        print("\n✅ URL Processing Successful!")
        print(f"   Document ID: {metadata.doc_id}")
        print(f"   Title: {metadata.title}")
        print(f"   Source: {metadata.source}")
        print(f"   Chunks created: {metadata.chunk_total}")
        print(f"   Created at: {metadata.created_at}")
        
        if metadata.description:
            print(f"   Description: {metadata.description}")
        
        if metadata.tags:
            print(f"   Tags: {', '.join(metadata.tags)}")
        
        # Show content preview
        print(f"\n   Content preview (first 200 chars):")
        print(f"   {processed_text[:200]}...")
        
        return metadata
        
    except Exception as e:
        print(f"\n❌ Error processing URL: {e}")
        logging.exception("URL processing failed")
        raise


def test_document_retrieval(document_service: DocumentService, doc_id: str):
    """
    Test document chunk retrieval.

    Args:
        document_service: DocumentService instance
        doc_id: Document ID to retrieve
    """
    print("\n" + "="*60)
    print("Testing Document Retrieval")
    print("="*60)
    
    try:
        print(f"\nRetrieving chunks for document: {doc_id}")
        chunks = document_service.get_document_chunks(doc_id)
        
        print(f"\n✅ Retrieved {len(chunks)} chunks")
        
        for i, (chunk_text, metadata) in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\n   Chunk {i}:")
            print(f"   - Length: {len(chunk_text)} chars")
            print(f"   - Preview: {chunk_text[:100]}...")
            print(f"   - Metadata: doc_id={metadata.get('doc_id')}, "
                  f"chunk_index={metadata.get('chunk_index')}")
        
        if len(chunks) > 3:
            print(f"\n   ... and {len(chunks) - 3} more chunks")
        
        return chunks
        
    except Exception as e:
        print(f"\n❌ Error retrieving document: {e}")
        logging.exception("Document retrieval failed")
        raise


def main():
    """Run all tests."""
    # Ensure directories exist
    print("Ensuring directories exist...")
    ensure_directories()
    print("✅ Directories ready")
    
    # Get device info (cached, fast)
    print("\nDetecting device...")
    device_info = get_device_info()
    print(f"✅ Device: {device_info['device']} (PyTorch: {device_info['torch_available']})")
    if device_info['cuda_available']:
        print(f"   GPU: {device_info['cuda_device_name']}")
    
    # Initialize document service
    print("\nInitializing DocumentService...")
    print("   (This will load the embedding model on first use)")
    document_service = DocumentService()
    print("✅ DocumentService initialized")
    
    # Pre-load embedding model to avoid loading during each test
    print("\nPre-loading embedding model (this may take a moment)...")
    try:
        _ = document_service.embedding_service.model  # Trigger model loading
        print("✅ Embedding model loaded and ready")
    except Exception as e:
        print(f"⚠️  Warning: Could not pre-load model: {e}")
        print("   Model will be loaded on first use")
    
    # Test PDF processing
    try:
        pdf_metadata = test_pdf_processing(document_service)
        
        # Test document retrieval
        test_document_retrieval(document_service, pdf_metadata.doc_id)
        
    except ImportError as e:
        print(f"\n⚠️  PDF processing test skipped: {e}")
        print("   Install reportlab to enable PDF testing: pip install reportlab")
    except Exception as e:
        print(f"\n⚠️  PDF processing test skipped: {e}")
    
    # Test Markdown processing
    try:
        markdown_metadata = test_markdown_processing(document_service)
        
        # Test document retrieval
        test_document_retrieval(document_service, markdown_metadata.doc_id)
        
    except Exception as e:
        print(f"\n⚠️  Markdown processing test skipped: {e}")
    
    # Test URL processing (optional, requires internet)
    try:
        url_metadata = test_url_processing(document_service)
        
        # Test document retrieval
        test_document_retrieval(document_service, url_metadata.doc_id)
        
    except Exception as e:
        print(f"\n⚠️  URL processing test skipped: {e}")
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)
    print("\nAll processed documents are stored in ChromaDB.")
    print("You can query them using the VectorService or RAG service.")


if __name__ == "__main__":
    main()

