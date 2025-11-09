"""Complete reindexing script to delete existing collections and regenerate all embeddings.

This script:
1. Deletes existing ChromaDB collections
2. Re-processes all documents from the documents/ directory (PDF and Markdown)
3. Re-vectorizes all notes from the notes/ directory
4. Uses the embedding model specified in .env file (EMBEDDING_MODEL)
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.document_service import DocumentService, DuplicateDocumentError
from backend.app.services.note_vectorization_service import NoteVectorizationService
from backend.app.services.vector_service import VectorService
from backend.app.utils.filesystem import DOCUMENTS_DIR, NOTES_DIR
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")


def delete_all_collections():
    """Delete all ChromaDB collections."""
    print("=" * 80)
    print("Step 1: Deleting existing collections")
    print("=" * 80)
    
    vector_service = VectorService()
    collections = vector_service.list_collections()
    
    if not collections:
        print("No collections found. Nothing to delete.")
        return
    
    print(f"Found {len(collections)} collection(s):")
    for coll_name in collections:
        collection = vector_service.get_or_create_collection(coll_name)
        count = collection.count()
        print(f"  - {coll_name}: {count} documents")
    
    print("\nDeleting collections...")
    for coll_name in collections:
        try:
            vector_service.delete_collection(coll_name)
            print(f"  ✓ Deleted: {coll_name}")
        except Exception as e:
            print(f"  ✗ Error deleting {coll_name}: {e}")
    
    print("\n✓ All collections deleted successfully.\n")


def reindex_documents():
    """Re-index all documents from documents/ directory."""
    print("=" * 80)
    print("Step 2: Re-indexing documents")
    print("=" * 80)
    
    doc_service = DocumentService()
    documents_dir = DOCUMENTS_DIR
    
    if not documents_dir.exists():
        print(f"Documents directory not found: {documents_dir}")
        return 0, 0, 0
    
    # Generate batch ID for this reindexing session
    batch_id = f"reindex_{uuid4().hex[:8]}"
    print(f"Batch ID: {batch_id}")
    print(f"Directory: {documents_dir}\n")
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    # Process PDF files
    pdf_files = sorted(documents_dir.glob("*.pdf"))
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF file(s):")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing PDF: {pdf_file.name}")
            try:
                metadata = doc_service.process_and_store_pdf(
                    pdf_file, skip_duplicates=False, import_batch=batch_id
                )
                imported_count += 1
                print(f"  ✓ Successfully indexed: {metadata.title}")
                print(f"    Doc ID: {metadata.doc_id}")
                print(f"    Chunks: {metadata.chunk_total}")
            except DuplicateDocumentError as e:
                skipped_count += 1
                print(f"  ⚠ Skipped (duplicate): {pdf_file.name}")
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error: {e}")
    
    # Process Markdown files
    md_files = sorted(documents_dir.glob("*.md"))
    if md_files:
        print(f"\nFound {len(md_files)} Markdown file(s):")
        for i, md_file in enumerate(md_files, 1):
            print(f"\n[{i}/{len(md_files)}] Processing Markdown: {md_file.name}")
            try:
                content = md_file.read_text(encoding="utf-8")
                metadata = doc_service.process_and_store_markdown(
                    content, str(md_file), skip_duplicates=False, import_batch=batch_id
                )
                imported_count += 1
                print(f"  ✓ Successfully indexed: {metadata.title}")
                print(f"    Doc ID: {metadata.doc_id}")
                print(f"    Chunks: {metadata.chunk_total}")
            except DuplicateDocumentError as e:
                skipped_count += 1
                print(f"  ⚠ Skipped (duplicate): {md_file.name}")
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error: {e}")
    
    if not pdf_files and not md_files:
        print("No PDF or Markdown files found in documents directory.")
    
    print("\n" + "-" * 80)
    print("Documents Summary:")
    print(f"  ✓ Successfully indexed: {imported_count}")
    print(f"  ⚠ Skipped (duplicates): {skipped_count}")
    print(f"  ✗ Errors: {error_count}")
    print("-" * 80 + "\n")
    
    return imported_count, skipped_count, error_count


def reindex_notes():
    """Re-vectorize all notes from notes/ directory."""
    print("=" * 80)
    print("Step 3: Re-vectorizing notes")
    print("=" * 80)
    
    notes_dir = NOTES_DIR
    
    if not notes_dir.exists():
        print(f"Notes directory not found: {notes_dir}")
        return 0, 0
    
    print(f"Directory: {notes_dir}\n")
    
    note_service = NoteVectorizationService()
    
    try:
        vectorized_count, skipped_count = note_service.vectorize_all_notes(
            force=True, incremental=False
        )
        
        print("\n" + "-" * 80)
        print("Notes Summary:")
        print(f"  ✓ Successfully vectorized: {vectorized_count}")
        print(f"  ⚠ Skipped: {skipped_count}")
        print("-" * 80 + "\n")
        
        return vectorized_count, skipped_count
    except Exception as e:
        print(f"\n✗ Error during note vectorization: {e}")
        return 0, 0


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("Complete Reindexing Script")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Delete all existing ChromaDB collections")
    print("  2. Re-index all documents from documents/ directory")
    print("  3. Re-vectorize all notes from notes/ directory")
    print("\n⚠️  WARNING: This will delete all existing embeddings!")
    print("   Make sure EMBEDDING_MODEL is set correctly in .env file")
    print("=" * 80 + "\n")
    
    # Confirm before proceeding
    try:
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("Cancelled.")
            return
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    # Step 1: Delete collections
    try:
        delete_all_collections()
    except Exception as e:
        print(f"✗ Error deleting collections: {e}")
        return
    
    # Step 2: Re-index documents
    try:
        doc_imported, doc_skipped, doc_errors = reindex_documents()
    except Exception as e:
        print(f"✗ Error re-indexing documents: {e}")
        doc_imported, doc_skipped, doc_errors = 0, 0, 0
    
    # Step 3: Re-vectorize notes
    try:
        note_vectorized, note_skipped = reindex_notes()
    except Exception as e:
        print(f"✗ Error re-vectorizing notes: {e}")
        note_vectorized, note_skipped = 0, 0
    
    # Final summary
    print("\n" + "=" * 80)
    print("Reindexing Complete!")
    print("=" * 80)
    print("\nDocuments:")
    print(f"  ✓ Indexed: {doc_imported}")
    print(f"  ⚠ Skipped: {doc_skipped}")
    print(f"  ✗ Errors: {doc_errors}")
    print("\nNotes:")
    print(f"  ✓ Vectorized: {note_vectorized}")
    print(f"  ⚠ Skipped: {note_skipped}")
    print("\n" + "=" * 80)
    print("✓ All embeddings regenerated with new model!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

