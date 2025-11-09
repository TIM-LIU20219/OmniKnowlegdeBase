"""Debug script to check what's actually stored."""

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

print(f"Total documents: {collection.count()}")

# Get ALL documents
all_results = collection.get(limit=1000, include=["metadatas", "documents"])

print(f"\nRetrieved {len(all_results.get('metadatas', []))} documents")

# Check for code files by examining file_path and source
code_count = 0
pdf_count = 0
other_count = 0

for meta in all_results.get("metadatas", []):
    file_path = meta.get("file_path", "")
    source = meta.get("source", "")
    
    if file_path.endswith(".py"):
        code_count += 1
        if code_count <= 3:
            print(f"\nCode file {code_count}:")
            print(f"  File: {file_path}")
            print(f"  Source: {source}")
            print(f"  Import batch: {meta.get('import_batch', 'N/A')}")
            code_keys = [k for k in meta.keys() if k.startswith("code_")]
            print(f"  Code metadata keys: {len(code_keys)}")
            if code_keys:
                for key in sorted(code_keys)[:5]:
                    print(f"    {key}: {meta[key]}")
    elif source == "pdf":
        pdf_count += 1
    else:
        other_count += 1

print(f"\nSummary:")
print(f"  Code files (.py): {code_count}")
print(f"  PDF files: {pdf_count}")
print(f"  Other files: {other_count}")

# Check import batches
batches = {}
for meta in all_results.get("metadatas", []):
    batch = meta.get("import_batch")
    if batch:
        batches[batch] = batches.get(batch, 0) + 1

print(f"\nImport batches: {batches}")


