"""Quick script to inspect stored metadata."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")

vector_service = VectorService()
collection = vector_service.get_or_create_collection("documents")

# Get samples with code metadata
results = collection.get(limit=100, include=["metadatas"])

print(f"Total documents in collection: {collection.count()}")
print("\nLooking for documents with code metadata...")

code_samples = []
for metadata in results.get("metadatas", []):
    code_keys = [k for k in metadata.keys() if k.startswith("code_")]
    if code_keys:
        code_samples.append(metadata)
        if len(code_samples) >= 3:
            break

# Get all documents and check for code files
print(f"Total documents in collection: {collection.count()}")

# Get all documents to find code files
all_results = collection.get(limit=500, include=["metadatas", "documents"])

print(f"\nChecking {len(all_results.get('metadatas', []))} documents...")

# Look for Python files or code-related content
code_files = []
for i, (meta, doc) in enumerate(zip(all_results.get("metadatas", []), all_results.get("documents", []))):
    file_path = meta.get("file_path", "")
    source = meta.get("source", "")
    
    # Check if it's a code file
    if (file_path.endswith(".py") or 
        source == "code" or 
        "systematically-improving-rag" in str(file_path).lower() or
        any(k.startswith("code_") for k in meta.keys())):
        code_files.append((meta, doc))
        if len(code_files) >= 5:
            break

if code_files:
    print(f"\n✅ Found {len(code_files)} potential code files")
    sample_meta, sample_doc = code_files[0]
    print("\nSample code file metadata:")
    for key in sorted(sample_meta.keys()):
        value = sample_meta[key]
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"  {key}: {value}")
    
    code_keys = [k for k in sample_meta.keys() if k.startswith("code_")]
    if code_keys:
        print(f"\n✅ Code metadata keys ({len(code_keys)}):")
        for key in sorted(code_keys):
            print(f"  {key}: {sample_meta[key]}")
    else:
        print("\n⚠️  No code_* metadata fields found!")
    
    print(f"\nDocument preview (first 300 chars):")
    print(f"  {sample_doc[:300]}...")
else:
    print("\n⚠️  No code files found in collection!")
    print("\nChecking document sources and file paths...")
    sources = {}
    file_extensions = {}
    for meta in all_results.get("metadatas", [])[:50]:
        source = meta.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
        file_path = meta.get("file_path", "")
        if file_path:
            ext = file_path.split(".")[-1] if "." in file_path else "no_ext"
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
    
    print(f"\nSources found: {sources}")
    print(f"File extensions: {file_extensions}")
    
    # Try to query by import_batch
    try:
        batch_results = collection.get(
            where={"import_batch": "systematically-improving-rag"},
            limit=5,
            include=["metadatas"]
        )
        if batch_results.get("metadatas"):
            print(f"\n✅ Found {len(batch_results['metadatas'])} documents with batch ID")
        else:
            print("\n⚠️  No documents found with batch 'systematically-improving-rag'")
    except Exception as e:
        print(f"\n❌ Error querying by batch: {e}")

