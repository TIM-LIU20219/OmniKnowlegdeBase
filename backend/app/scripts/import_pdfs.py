"""Script to batch import PDF files."""

import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.document_service import DocumentService, DuplicateDocumentError
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")


def import_pdfs_from_directory(
    directory: Path, skip_duplicates: bool = True, batch_id: str = None
) -> list:
    """
    Import all PDF files from a directory.

    Args:
        directory: Directory containing PDF files
        skip_duplicates: If True, skip files that already exist
        batch_id: Optional batch identifier for tracking

    Returns:
        List of imported document metadata
    """
    doc_service = DocumentService()
    imported_docs = []
    skipped_docs = []
    error_docs = []

    # Generate batch ID if not provided
    if batch_id is None:
        batch_id = f"batch_{uuid4().hex[:8]}"

    # Find all PDF files
    pdf_files = sorted(directory.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return imported_docs

    print(f"Found {len(pdf_files)} PDF files to import")
    print(f"Batch ID: {batch_id}")
    print(f"Skip duplicates: {skip_duplicates}\n")
    print("=" * 60)

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-" * 60)

        try:
            metadata = doc_service.process_and_store_pdf(
                pdf_file, skip_duplicates=skip_duplicates, import_batch=batch_id
            )
            imported_docs.append(metadata)

            print(f"✓ Successfully imported: {metadata.title}")
            print(f"  Doc ID: {metadata.doc_id}")
            print(f"  Chunks: {metadata.chunk_total}")
            print(f"  Source: {metadata.source}")
            if metadata.original_path:
                print(f"  Original path: {metadata.original_path}")
            if metadata.file_hash:
                print(f"  File hash: {metadata.file_hash[:8]}...")

        except DuplicateDocumentError as e:
            skipped_docs.append((pdf_file.name, e.existing_doc))
            print(f"⚠ Skipped (duplicate): {pdf_file.name}")
            if e.existing_doc:
                print(f"  Existing doc ID: {e.existing_doc.doc_id}")
                print(f"  Existing title: {e.existing_doc.title}")

        except Exception as e:
            error_docs.append((pdf_file.name, str(e)))
            print(f"✗ Error importing {pdf_file.name}: {e}")
            continue

    return imported_docs, skipped_docs, error_docs


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch import PDF files")
    parser.add_argument(
        "--directory",
        type=str,
        default="resources/FoundationOfLLMs",
        help="Directory containing PDF files (default: resources/FoundationOfLLMs)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Single PDF file to import",
    )
    parser.add_argument(
        "--skip-duplicates",
        action="store_true",
        default=True,
        help="Skip files that already exist (default: True)",
    )
    parser.add_argument(
        "--no-skip-duplicates",
        dest="skip_duplicates",
        action="store_false",
        help="Allow duplicate files to be imported",
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        help="Batch identifier for tracking import groups (auto-generated if not provided)",
    )

    args = parser.parse_args()

    doc_service = DocumentService()

    # Generate batch ID if not provided
    batch_id = args.batch_id or f"batch_{uuid4().hex[:8]}"

    if args.file:
        # Import single file
        pdf_file = Path(args.file)
        if not pdf_file.exists():
            print(f"Error: File not found: {pdf_file}")
            return

        print(f"Importing: {pdf_file.name}")
        print(f"Batch ID: {batch_id}")
        print(f"Skip duplicates: {args.skip_duplicates}\n")

        try:
            metadata = doc_service.process_and_store_pdf(
                pdf_file, skip_duplicates=args.skip_duplicates, import_batch=batch_id
            )
            print(f"✓ Successfully imported: {metadata.title}")
            print(f"  Doc ID: {metadata.doc_id}")
            print(f"  Chunks: {metadata.chunk_total}")
            if metadata.original_path:
                print(f"  Original path: {metadata.original_path}")
            if metadata.file_hash:
                print(f"  File hash: {metadata.file_hash[:8]}...")

        except DuplicateDocumentError as e:
            print(f"⚠ Skipped (duplicate): {pdf_file.name}")
            if e.existing_doc:
                print(f"  Existing doc ID: {e.existing_doc.doc_id}")
                print(f"  Existing title: {e.existing_doc.title}")

        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        # Import from directory
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory not found: {directory}")
            return

        imported_docs, skipped_docs, error_docs = import_pdfs_from_directory(
            directory, skip_duplicates=args.skip_duplicates, batch_id=batch_id
        )

        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"Batch ID: {batch_id}")
        print(f"Total files processed: {len(imported_docs) + len(skipped_docs) + len(error_docs)}")
        print(f"  ✓ Successfully imported: {len(imported_docs)}")
        print(f"  ⚠ Skipped (duplicates): {len(skipped_docs)}")
        print(f"  ✗ Errors: {len(error_docs)}")

        total_chunks = sum(doc.chunk_total or 0 for doc in imported_docs)
        print(f"\nTotal chunks created: {total_chunks}")

        if imported_docs:
            print("\nImported documents:")
            for doc in imported_docs:
                print(f"  - {doc.title} (ID: {doc.doc_id}, Chunks: {doc.chunk_total})")

        if skipped_docs:
            print("\nSkipped documents (duplicates):")
            for filename, existing_doc in skipped_docs:
                print(f"  - {filename} (existing: {existing_doc.doc_id if existing_doc else 'unknown'})")

        if error_docs:
            print("\nFailed documents:")
            for filename, error_msg in error_docs:
                print(f"  - {filename}: {error_msg}")


if __name__ == "__main__":
    main()

