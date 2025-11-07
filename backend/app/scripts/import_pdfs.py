"""Script to batch import PDF files."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.document_service import DocumentService
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")


def import_pdfs_from_directory(directory: Path) -> list:
    """
    Import all PDF files from a directory.

    Args:
        directory: Directory containing PDF files

    Returns:
        List of imported document metadata
    """
    doc_service = DocumentService()
    imported_docs = []

    # Find all PDF files
    pdf_files = sorted(directory.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return imported_docs

    print(f"Found {len(pdf_files)} PDF files to import\n")
    print("=" * 60)

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-" * 60)

        try:
            metadata = doc_service.process_and_store_pdf(pdf_file)
            imported_docs.append(metadata)

            print(f"✓ Successfully imported: {metadata.title}")
            print(f"  Doc ID: {metadata.doc_id}")
            print(f"  Chunks: {metadata.chunk_total}")
            print(f"  Source: {metadata.source}")

        except Exception as e:
            print(f"✗ Error importing {pdf_file.name}: {e}")
            continue

    return imported_docs


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

    args = parser.parse_args()

    doc_service = DocumentService()

    if args.file:
        # Import single file
        pdf_file = Path(args.file)
        if not pdf_file.exists():
            print(f"Error: File not found: {pdf_file}")
            return

        print(f"Importing: {pdf_file.name}")
        try:
            metadata = doc_service.process_and_store_pdf(pdf_file)
            print(f"✓ Successfully imported: {metadata.title}")
            print(f"  Doc ID: {metadata.doc_id}")
            print(f"  Chunks: {metadata.chunk_total}")
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        # Import from directory
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory not found: {directory}")
            return

        imported_docs = import_pdfs_from_directory(directory)

        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"Total files processed: {len(imported_docs)}")
        total_chunks = sum(doc.chunk_total or 0 for doc in imported_docs)
        print(f"Total chunks created: {total_chunks}")

        if imported_docs:
            print("\nImported documents:")
            for doc in imported_docs:
                print(f"  - {doc.title} (ID: {doc.doc_id}, Chunks: {doc.chunk_total})")


if __name__ == "__main__":
    main()

