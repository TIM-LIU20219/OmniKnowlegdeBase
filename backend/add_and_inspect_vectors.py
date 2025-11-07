"""Script to add test document and then inspect ChromaDB vectors."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.models.metadata import DocumentMetadata, DocType, SourceType
from backend.app.services.document_service import DocumentService
from backend.app.utils.logging_config import setup_logging
from datetime import datetime

# Setup logging
setup_logging(log_level="INFO")

print("=" * 80)
print("Adding Test Document and Inspecting ChromaDB Vectors")
print("=" * 80)

# Initialize document service
print("\n1. Initializing DocumentService...")
doc_service = DocumentService()

# Create test document
print("\n2. Creating and processing test document...")
test_content = """
# RAG System Architecture

## Overview
This document describes the RAG (Retrieval-Augmented Generation) system architecture.

## Components

### 1. Document Processing
- **Chunking Service**: Splits documents into chunks with configurable size and overlap
- **Default chunk size**: 1000 characters
- **Default overlap**: 200 characters

### 2. Embedding Service
- Uses SentenceTransformer models for generating embeddings
- Default model: all-MiniLM-L6-v2
- Supports GPU acceleration when available

### 3. Vector Storage
- ChromaDB for storing document vectors
- Collections: documents and notes
- Metadata filtering supported

### 4. Retrieval
- Semantic search using vector similarity
- Configurable number of results (k parameter)
- Similarity threshold filtering

### 5. Generation
- LLM integration via LangChain
- Supports multiple providers (DeepSeek, OpenAI, OpenRouter)
- Stream response support
"""

# Create metadata
metadata = DocumentMetadata(
    doc_id="test_rag_doc_001",
    doc_type=DocType.DOCUMENT,
    title="RAG System Architecture",
    created_at=datetime.now().isoformat(),
    source=SourceType.MARKDOWN,
    tags=["rag", "architecture", "test"],
    description="Test document for RAG system",
)

# Process and store
print(f"   Processing document: {metadata.title}")
result_metadata = doc_service.process_and_store_markdown(test_content, file_path="test_rag.md")

print(f"\n[OK] Document processed: {result_metadata.chunk_total} chunks created")

# Now inspect ChromaDB
print("\n" + "=" * 80)
print("Inspecting ChromaDB Vector Storage")
print("=" * 80)

from backend.app.services.vector_service import VectorService

vector_service = VectorService()
collection = vector_service.get_or_create_collection("documents")

print(f"\nCollection: documents")
print(f"Count: {collection.count()} document chunks\n")

# Get all documents
results = collection.get()

if not results or not results.get("ids") or len(results["ids"]) == 0:
    print("No documents found.")
    sys.exit(0)

ids = results["ids"]
documents = results.get("documents", [])
metadatas = results.get("metadatas", [])
embeddings = results.get("embeddings", [])

print(f"Found {len(ids)} document chunks\n")

# Display first document in detail
if len(ids) > 0:
    print("-" * 80)
    print("First Document Chunk (Detailed View)")
    print("-" * 80)
    print(f"ID: {ids[0]}")
    print(f"\nMetadata:")
    for key, value in metadatas[0].items():
        print(f"  {key}: {value}")
    
    print(f"\nText Content:")
    print(f"  {documents[0]}")
    print(f"\nText Length: {len(documents[0])} characters")
    
    if embeddings and len(embeddings) > 0:
        emb = embeddings[0]
        print(f"\n{'=' * 80}")
        print("Embedding Vector Details")
        print("=" * 80)
        print(f"Dimension: {len(emb)}")
        print(f"\nStatistics:")
        print(f"  Min value: {min(emb):.8f}")
        print(f"  Max value: {max(emb):.8f}")
        print(f"  Mean value: {sum(emb)/len(emb):.8f}")
        print(f"  Std deviation: {(sum((x - sum(emb)/len(emb))**2 for x in emb) / len(emb))**0.5:.8f}")
        
        print(f"\nFirst 20 values:")
        for i in range(min(20, len(emb))):
            print(f"  [{i:3d}]: {emb[i]:.8f}")
        
        print(f"\nLast 20 values:")
        for i in range(max(0, len(emb)-20), len(emb)):
            print(f"  [{i:3d}]: {emb[i]:.8f}")
        
        # Save full vector to file
        vector_file = Path("backend/sample_vector.txt")
        with open(vector_file, "w", encoding="utf-8") as f:
            f.write(f"Sample Embedding Vector from ChromaDB\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(f"Document ID: {ids[0]}\n")
            f.write(f"Metadata: {metadatas[0]}\n")
            f.write(f"\nDocument Text:\n{documents[0]}\n")
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Vector Dimension: {len(emb)}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write("Full Vector Values:\n")
            f.write("-" * 80 + "\n")
            for i, val in enumerate(emb):
                f.write(f"{i:4d}: {val:.10f}\n")
        
        print(f"\n[Saved] Full vector saved to: {vector_file}")
        print(f"   You can open this file to see all {len(emb)} vector values")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"Total chunks: {len(ids)}")
if embeddings:
    print(f"All vectors have dimension: {len(embeddings[0])}")
    print(f"Embedding model: all-MiniLM-L6-v2 (384 dimensions)")
print("=" * 80)

