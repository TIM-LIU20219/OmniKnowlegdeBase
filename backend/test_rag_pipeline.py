"""Test script for RAG pipeline."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

# Setup logging
setup_logging(log_level="INFO")

print("=" * 60)
print("RAG Pipeline Test")
print("=" * 60)

# Initialize services
print("\n1. Initializing services...")
try:
    vector_service = VectorService()
    print("   ✓ VectorService initialized")
except Exception as e:
    print(f"   ✗ VectorService failed: {e}")
    sys.exit(1)

try:
    embedding_service = EmbeddingService()
    print("   ✓ EmbeddingService initialized")
except Exception as e:
    print(f"   ✗ EmbeddingService failed: {e}")
    sys.exit(1)

try:
    llm_service = LLMService()
    print("   ✓ LLMService initialized")
except Exception as e:
    print(f"   ✗ LLMService failed: {e}")
    print("   Hint: Make sure DEEPSEEK_API_KEY is set in .env file")
    sys.exit(1)

# Create RAG service
print("\n2. Creating RAG service...")
try:
    rag_service = RAGService(
        vector_service=vector_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        collection_name="documents",
        k=4,
    )
    print("   ✓ RAGService initialized")
except Exception as e:
    print(f"   ✗ RAGService failed: {e}")
    sys.exit(1)

# Test query
print("\n3. Testing RAG query...")
test_question = "What is the default chunk size?"

print(f"   Question: {test_question}")
print("   Running query...")

try:
    result = rag_service.query(test_question)
    
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"\nAnswer:")
    print(result.get("answer", "No answer generated"))
    
    print(f"\nRetrieved Documents: {result.get('metadata', {}).get('retrieved_count', 0)}")
    
    sources = result.get("sources", [])
    if sources:
        print("\nSources:")
        for i, source in enumerate(sources[:3], 1):  # Show first 3 sources
            print(f"  {i}. {source.get('title', 'Unknown')} (ID: {source.get('doc_id', 'N/A')})")
    
    print("\n" + "=" * 60)
    print("✓ RAG Pipeline test completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

