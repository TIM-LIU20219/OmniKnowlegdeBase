"""Tool to check and diagnose embedding dimension mismatches."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.services.vector_service import VectorService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")

def check_embedding_dimensions():
    """Check embedding dimensions for all collections."""
    print("=" * 80)
    print("Embedding Dimension Checker")
    print("=" * 80)
    
    vs = VectorService()
    es = EmbeddingService()
    
    # Get current model dimension
    current_dim = es.get_embedding_dimension()
    print(f"\nCurrent Embedding Model: {es.model_name}")
    print(f"Current Model Dimension: {current_dim}")
    
    # Check all collections
    collections = vs.list_collections()
    print(f"\nChecking {len(collections)} collection(s)...")
    print("-" * 80)
    
    all_match = True
    for collection_name in collections:
        coll_dim = vs.get_collection_embedding_dimension(collection_name)
        if coll_dim is None:
            print(f"  {collection_name}: Empty collection (no dimension check needed)")
            continue
        
        match = coll_dim == current_dim
        status = "✅ MATCH" if match else "❌ MISMATCH"
        print(f"  {collection_name}: {coll_dim}D {status}")
        
        if not match:
            all_match = False
            print(f"    ⚠️  Collection expects {coll_dim}D, but model generates {current_dim}D")
    
    print("-" * 80)
    
    if all_match:
        print("\n✅ All collections match current embedding model dimension!")
    else:
        print("\n⚠️  Dimension mismatches detected!")
        print("\nSolutions:")
        print("  1. Set EMBEDDING_MODEL in .env to match the model used for indexing")
        print("  2. Re-index all documents with the current model")
        print("  3. Use a different collection name for new documents")
        print("\nCommon embedding models and dimensions:")
        print("  - all-MiniLM-L6-v2: 384 dimensions")
        print("  - BAAI/bge-small-zh-v1.5: 512 dimensions")
        print("  - BAAI/bge-base-zh-v1.5: 768 dimensions")
    
    print("=" * 80)

if __name__ == "__main__":
    check_embedding_dimensions()


