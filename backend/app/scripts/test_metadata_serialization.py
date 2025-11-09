"""Debug script to check if code files are being stored correctly."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.models.metadata import DocumentMetadata, SourceType, DocType
from backend.app.models.metadata import CodeMetadata

# Test metadata serialization
test_metadata = DocumentMetadata(
    doc_id="test-123",
    doc_type=DocType.DOCUMENT,
    file_path="test.py",
    title="test.py",
    source=SourceType.CODE,
    import_batch="test-batch",
    code_metadata=CodeMetadata(
        file_type="python",
        language="python",
        function_name="test_function",
        code_type="function"
    )
)

chroma_meta = test_metadata.to_chromadb_metadata()
print("Test metadata serialization:")
print(f"  import_batch: {chroma_meta.get('import_batch')}")
print(f"  source: {chroma_meta.get('source')}")
code_keys = [k for k in chroma_meta.keys() if k.startswith("code_")]
print(f"  code_* keys: {code_keys}")
print(f"\nFull metadata:")
for k, v in sorted(chroma_meta.items()):
    print(f"  {k}: {v}")


