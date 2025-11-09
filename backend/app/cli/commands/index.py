"""Index management CLI commands."""

import json
from pathlib import Path
from uuid import uuid4

import click

from backend.app.services.document_service import DocumentService, DuplicateDocumentError
from backend.app.services.note_vectorization_service import NoteVectorizationService
from backend.app.services.vector_service import VectorService
from backend.app.utils.filesystem import RESOURCES_DIR, NOTES_DIR
from backend.app.utils.file_hash import get_file_hash_and_metadata


@click.group(name="index")
def index_group():
    """Index management commands."""
    pass


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
    """Re-index all documents from resources/ directory."""
    print("=" * 80)
    print("Step 2: Re-indexing documents")
    print("=" * 80)
    
    doc_service = DocumentService()
    resources_dir = RESOURCES_DIR
    
    if not resources_dir.exists():
        print(f"Resources directory not found: {resources_dir}")
        return 0, 0, 0
    
    # Generate batch ID for this reindexing session
    batch_id = f"reindex_{uuid4().hex[:8]}"
    print(f"Batch ID: {batch_id}")
    print(f"Directory: {resources_dir}\n")
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    # Define file extensions to process
    pdf_extensions = ["*.pdf"]
    markdown_extensions = ["*.md"]
    code_extensions = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.go", "*.rs", "*.rb", "*.php"]
    
    # Process PDF files recursively
    pdf_files = []
    for ext in pdf_extensions:
        pdf_files.extend(resources_dir.rglob(ext))
    pdf_files = sorted(set(pdf_files))
    
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF file(s):")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing PDF: {pdf_file.relative_to(resources_dir)}")
            try:
                # Calculate file hash first
                file_info = get_file_hash_and_metadata(pdf_file)
                file_hash = file_info["file_hash"]
                
                # Delete existing document with same hash to avoid duplicates
                deleted = doc_service.delete_document_by_hash(file_hash)
                if deleted:
                    print(f"  ℹ Deleted existing document with same hash")
                
                metadata = doc_service.process_and_store_pdf(
                    pdf_file, skip_duplicates=False, import_batch=batch_id
                )
                imported_count += 1
                print(f"  ✓ Successfully indexed: {metadata.title}")
                print(f"    Doc ID: {metadata.doc_id}")
                print(f"    Source: {metadata.source}")
                print(f"    Chunks: {metadata.chunk_total}")
            except DuplicateDocumentError as e:
                skipped_count += 1
                print(f"  ⚠ Skipped (duplicate): {pdf_file.name}")
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error: {e}")
    
    # Process Markdown and code files recursively
    md_and_code_files = []
    for ext in markdown_extensions + code_extensions:
        md_and_code_files.extend(resources_dir.rglob(ext))
    md_and_code_files = sorted(set(md_and_code_files))
    
    if md_and_code_files:
        print(f"\nFound {len(md_and_code_files)} Markdown/Code file(s):")
        for i, md_file in enumerate(md_and_code_files, 1):
            file_type = "Code" if md_file.suffix.lower() in [ext.replace("*", "") for ext in code_extensions] else "Markdown"
            print(f"\n[{i}/{len(md_and_code_files)}] Processing {file_type}: {md_file.relative_to(resources_dir)}")
            try:
                # Calculate file hash first
                file_info = get_file_hash_and_metadata(md_file)
                file_hash = file_info["file_hash"]
                
                # Delete existing document with same hash to avoid duplicates
                deleted = doc_service.delete_document_by_hash(file_hash)
                if deleted:
                    print(f"  ℹ Deleted existing document with same hash")
                
                content = md_file.read_text(encoding="utf-8")
                metadata = doc_service.process_and_store_markdown(
                    content, str(md_file), skip_duplicates=False, import_batch=batch_id
                )
                imported_count += 1
                print(f"  ✓ Successfully indexed: {metadata.title}")
                print(f"    Doc ID: {metadata.doc_id}")
                print(f"    Doc Type: {metadata.doc_type}")
                print(f"    Source: {metadata.source}")
                print(f"    Chunks: {metadata.chunk_total}")
            except DuplicateDocumentError as e:
                skipped_count += 1
                print(f"  ⚠ Skipped (duplicate): {md_file.name}")
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error: {e}")
    
    if not pdf_files and not md_and_code_files:
        print("No PDF, Markdown, or code files found in resources directory.")
    
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


@index_group.command(name="reindex")
@click.option("--documents", is_flag=True, help="Re-index documents only")
@click.option("--notes", is_flag=True, help="Re-index notes only")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def reindex(documents, notes, yes):
    """
    Re-index all documents and/or notes.
    
    If neither --documents nor --notes is specified, both will be re-indexed.
    """
    # Determine what to re-index
    index_docs = documents or (not documents and not notes)
    index_notes = notes or (not documents and not notes)
    
    if not yes:
        msg = "This will delete existing embeddings and re-index "
        if index_docs and index_notes:
            msg += "all documents and notes"
        elif index_docs:
            msg += "all documents"
        else:
            msg += "all notes"
        msg += ". Continue?"
        click.confirm(msg, abort=True)
    
    try:
        if index_docs and index_notes:
            # Delete all collections first
            delete_all_collections()
            doc_imported, doc_skipped, doc_errors = reindex_documents()
            note_vectorized, note_skipped = reindex_notes()
            
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
            print("✓ All embeddings regenerated!")
            print("=" * 80 + "\n")
        elif index_docs:
            # Only delete documents collection
            vector_service = VectorService()
            collection_name = vector_service.collection_names["documents"]
            try:
                vector_service.delete_collection(collection_name)
                click.echo(f"✓ Deleted collection: {collection_name}")
            except Exception as e:
                click.echo(f"⚠ Collection not found or error: {e}")
            doc_imported, doc_skipped, doc_errors = reindex_documents()
            click.echo(f"\n✓ Documents re-indexed: {doc_imported} indexed, {doc_skipped} skipped, {doc_errors} errors")
        else:
            # Only re-index notes (don't delete collections)
            note_vectorized, note_skipped = reindex_notes()
            click.echo(f"\n✓ Notes re-indexed: {note_vectorized} vectorized, {note_skipped} skipped")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@index_group.command(name="clean")
@click.option("--chromadb", is_flag=True, help="Delete ChromaDB data")
@click.option("--sqlite", is_flag=True, help="Delete SQLite database")
@click.option("--all", "all_databases", is_flag=True, help="Delete all databases")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def clean(chromadb, sqlite, all_databases, yes):
    """
    Clean databases (delete all data).
    
    WARNING: This will permanently delete all indexed data!
    """
    from backend.app.utils.filesystem import BASE_DIR
    from backend.app.utils.chromadb_config import chromadb_config
    import shutil
    
    if all_databases:
        chromadb = True
        sqlite = True
    
    if not chromadb and not sqlite:
        click.echo("Error: Specify --chromadb, --sqlite, or --all", err=True)
        raise click.Abort()
    
    if not yes:
        msg = "This will permanently delete "
        if chromadb and sqlite:
            msg += "all databases (ChromaDB and SQLite)"
        elif chromadb:
            msg += "ChromaDB data"
        else:
            msg += "SQLite database"
        msg += ". Continue?"
        click.confirm(msg, abort=True)
    
    try:
        if chromadb:
            # Delete ChromaDB directory
            chroma_path = chromadb_config.persist_directory
            if chroma_path.exists():
                shutil.rmtree(chroma_path)
                click.echo(f"✓ Deleted ChromaDB directory: {chroma_path}")
            else:
                click.echo(f"⚠ ChromaDB directory not found: {chroma_path}")
        
        if sqlite:
            # Delete SQLite database
            db_path = BASE_DIR / "backend" / "app" / "db" / "notes.db"
            if db_path.exists():
                db_path.unlink()
                click.echo(f"✓ Deleted SQLite database: {db_path}")
            else:
                click.echo(f"⚠ SQLite database not found: {db_path}")
        
        click.echo("\n✓ Database cleanup complete!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@index_group.command(name="status")
def status():
    """Show index status."""
    from backend.app.services.vector_service import VectorService
    from backend.app.services.chromadb_metadata_service import ChromaDBMetadataService
    from backend.app.utils.filesystem import BASE_DIR
    
    vector_service = VectorService()
    metadata_service = ChromaDBMetadataService()
    
    # ChromaDB status
    click.echo("ChromaDB Status:")
    click.echo(f"  Location: {vector_service.config.persist_directory}")
    collections = vector_service.list_collections()
    if collections:
        collection = None
        for coll_name in collections:
            coll = vector_service.get_or_create_collection(coll_name)
            count = coll.count()
            click.echo(f"  Collection '{coll_name}': {count} documents")
            if not collection:
                collection = coll
        
        # Get unique document count
        if collection:
            try:
                all_docs = collection.get(include=["metadatas"])
                if all_docs.get("metadatas"):
                    unique_doc_ids = set()
                    for metadata in all_docs["metadatas"]:
                        doc_id = metadata.get("doc_id")
                        if doc_id:
                            unique_doc_ids.add(doc_id)
                    click.echo(f"  Unique documents: {len(unique_doc_ids)}")
            except Exception:
                pass
            
            # Notes count
            try:
                all_notes = collection.get(where={"doc_type": "note"}, include=["metadatas"])
                if all_notes.get("metadatas"):
                    unique_note_ids = set()
                    for metadata in all_notes["metadatas"]:
                        doc_id = metadata.get("doc_id")
                        if doc_id:
                            unique_note_ids.add(doc_id)
                    click.echo(f"\nNotes: {len(unique_note_ids)}")
            except Exception:
                pass
    else:
        click.echo("  No collections found")
    
    # SQLite status (deprecated)
    click.echo("\nSQLite Status (deprecated):")
    db_path = BASE_DIR / "backend" / "app" / "db" / "notes.db"
    click.echo(f"  Location: {db_path}")
    if db_path.exists():
        click.echo(f"  Database exists (deprecated, using ChromaDB now)")
    else:
        click.echo("  Database not found")

