"""Script to inspect ChromaDB vector storage."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

# Setup logging
setup_logging(log_level="INFO")

print("=" * 80)
print("ChromaDB Vector Storage Inspector")
print("=" * 80)

# Initialize vector service
vector_service = VectorService()

# List all collections first
print("\nAvailable collections:")
all_collections = vector_service.list_collections()
for col_name in all_collections:
    col = vector_service.get_or_create_collection(col_name)
    count = col.count()
    print(f"  - {col_name}: {count} documents")

# Get collection
collection_name = "documents"
collection = vector_service.get_or_create_collection(collection_name)

print(f"\n{'=' * 80}")
print(f"Inspecting collection: {collection_name}")
print(f"Count: {collection.count()} documents")
print("=" * 80)

# Get all documents
print("=" * 80)
print("Retrieving all documents from ChromaDB...")
print("=" * 80)

try:
    # Query all documents - need to explicitly include embeddings
    # ChromaDB doesn't return embeddings by default, need to specify include=['embeddings']
    results = collection.get(include=['documents', 'metadatas', 'embeddings'])
    
    if not results or not results.get("ids") or len(results["ids"]) == 0:
        print("No documents found in collection.")
        sys.exit(0)
    
    ids = results["ids"]
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    embeddings = results.get("embeddings", [])
    
    print(f"\nFound {len(ids)} document chunks\n")
    
    # Display each document
    for i, (doc_id, doc_text, metadata, embedding) in enumerate(
        zip(ids, documents, metadatas, embeddings), 1
    ):
        print("-" * 80)
        print(f"Document {i}/{len(ids)}")
        print("-" * 80)
        print(f"ID: {doc_id}")
        print(f"\nMetadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print(f"\nText Content (first 500 chars):")
        print(f"  {doc_text[:500]}{'...' if len(doc_text) > 500 else ''}")
        print(f"\nText Length: {len(doc_text)} characters")
        
        if embedding is not None:
            import numpy as np
            # Convert to list if numpy array
            if isinstance(embedding, np.ndarray):
                emb_list = embedding.tolist()
            else:
                emb_list = list(embedding) if embedding else []
            
            if len(emb_list) > 0:
                print(f"\nEmbedding Vector:")
                print(f"  Dimension: {len(emb_list)}")
                print(f"  First 10 values: {[f'{v:.6f}' for v in emb_list[:10]]}")
                print(f"  Last 10 values: {[f'{v:.6f}' for v in emb_list[-10:]]}")
                print(f"  Min value: {min(emb_list):.6f}")
                print(f"  Max value: {max(emb_list):.6f}")
                print(f"  Mean value: {sum(emb_list)/len(emb_list):.6f}")
                print(f"  Std deviation: {(sum((x - sum(emb_list)/len(emb_list))**2 for x in emb_list) / len(emb_list))**0.5:.6f}")
                
                # Option to save full vector
                if i == 1:  # Only show option for first document
                    print(f"\n  Tip: Full vector data can be saved to a file if needed")
        
        print()
    
    # Summary statistics
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    
    if embeddings and len(embeddings) > 0:
        import numpy as np
        all_dims = []
        for emb in embeddings:
            if emb is not None:
                if isinstance(emb, np.ndarray):
                    all_dims.append(len(emb))
                else:
                    all_dims.append(len(emb))
        
        if all_dims:
            print(f"Embedding dimensions: {set(all_dims)}")
            print(f"Total vectors: {len([e for e in embeddings if e is not None])}")
        
        # Calculate some statistics across all embeddings
        all_values = []
        for emb in embeddings:
            if emb is not None:
                if isinstance(emb, np.ndarray):
                    all_values.extend(emb.tolist())
                else:
                    all_values.extend(list(emb))
        
        if all_values:
            print(f"\nAcross all embeddings:")
            print(f"  Total values: {len(all_values)}")
            print(f"  Min: {min(all_values):.6f}")
            print(f"  Max: {max(all_values):.6f}")
            print(f"  Mean: {sum(all_values)/len(all_values):.6f}")
    
    # Document statistics
    doc_lengths = [len(doc) for doc in documents]
    print(f"\nText statistics:")
    print(f"  Total chunks: {len(documents)}")
    print(f"  Average length: {sum(doc_lengths)/len(doc_lengths):.1f} chars")
    print(f"  Min length: {min(doc_lengths)} chars")
    print(f"  Max length: {max(doc_lengths)} chars")
    
    # Group by document ID
    doc_groups = {}
    for doc_id, metadata in zip(ids, metadatas):
        doc_id_base = metadata.get("doc_id", doc_id.split("_chunk_")[0])
        if doc_id_base not in doc_groups:
            doc_groups[doc_id_base] = []
        doc_groups[doc_id_base].append(doc_id)
    
    print(f"\nDocuments grouped by doc_id:")
    for doc_id_base, chunk_ids in doc_groups.items():
        print(f"  {doc_id_base}: {len(chunk_ids)} chunks")
    
    # Save sample vector to file for inspection
    if embeddings and len(embeddings) > 0:
        sample_vector = embeddings[0]
        vector_file = Path("sample_vector.txt")
        with open(vector_file, "w", encoding="utf-8") as f:
            f.write(f"Sample Embedding Vector\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Dimension: {len(sample_vector)}\n")
            f.write(f"Document ID: {ids[0]}\n")
            f.write(f"Document Text: {documents[0][:200]}...\n")
            f.write(f"\nFull Vector Values:\n")
            for i, val in enumerate(sample_vector):
                f.write(f"{i:4d}: {val:.8f}\n")
        print(f"\n💾 Sample vector saved to: {vector_file}")
    
    print("\n" + "=" * 80)
    print("Inspection complete!")
    print("=" * 80)

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

