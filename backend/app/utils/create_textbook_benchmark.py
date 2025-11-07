"""Tool for creating benchmark dataset from PDF textbook."""

import json
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.models.benchmark import BenchmarkDataset, BenchmarkQuestion
from backend.app.services.benchmark_evaluator import save_benchmark_dataset
from backend.app.services.document_service import DocumentService
from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

setup_logging(log_level="INFO")


def list_documents() -> List[dict]:
    """
    List all documents in ChromaDB.

    Returns:
        List of document metadata dictionaries
    """
    vector_service = VectorService()
    collection = vector_service.get_documents_collection()

    # Get all documents
    results = collection.get()

    if not results or not results.get("ids"):
        return []

    # Group chunks by doc_id
    doc_map = {}
    ids = results["ids"]
    metadatas = results.get("metadatas", [])

    for chunk_id, metadata in zip(ids, metadatas):
        doc_id = metadata.get("doc_id")
        if doc_id and doc_id not in doc_map:
            doc_map[doc_id] = {
                "doc_id": doc_id,
                "title": metadata.get("title", "Unknown"),
                "source": metadata.get("source", "unknown"),
                "chunk_count": 0,
            }
        if doc_id:
            doc_map[doc_id]["chunk_count"] += 1

    return list(doc_map.values())


def search_documents_by_content(query: str, limit: int = 5) -> List[dict]:
    """
    Search documents by content to find relevant doc_ids.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        List of document metadata with relevance scores
    """
    from backend.app.services.embedding_service import EmbeddingService

    vector_service = VectorService()
    embedding_service = EmbeddingService()

    # Generate query embedding
    query_embedding = embedding_service.embed_text(query)

    # Query ChromaDB
    results = vector_service.query(
        collection_name="documents",
        query_embeddings=[query_embedding],
        n_results=limit,
    )

    if not results or not results.get("ids"):
        return []

    # Extract unique doc_ids
    doc_map = {}
    ids = results["ids"][0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for chunk_id, metadata, distance in zip(ids, metadatas, distances):
        doc_id = metadata.get("doc_id")
        if doc_id and doc_id not in doc_map:
            doc_map[doc_id] = {
                "doc_id": doc_id,
                "title": metadata.get("title", "Unknown"),
                "source": metadata.get("source", "unknown"),
                "relevance_score": 1.0 - distance,  # Convert distance to similarity
            }

    return list(doc_map.values())


def create_question_interactive() -> Optional[BenchmarkQuestion]:
    """
    Interactively create a benchmark question.

    Returns:
        BenchmarkQuestion or None if cancelled
    """
    print("\n" + "=" * 60)
    print("Create New Question")
    print("=" * 60)

    # Get question ID
    question_id = input("\nQuestion ID (e.g., textbook_001): ").strip()
    if not question_id:
        print("Question ID is required. Cancelled.")
        return None

    # Get question text
    print("\nEnter the question:")
    question = input("> ").strip()
    if not question:
        print("Question text is required. Cancelled.")
        return None

    # Get ground truth answer
    print("\nEnter the ground truth answer:")
    ground_truth = input("> ").strip()
    if not ground_truth:
        print("Ground truth answer is required. Cancelled.")
        return None

    # Search for relevant documents
    print("\nSearching for relevant documents...")
    relevant_docs = search_documents_by_content(question, limit=10)

    if relevant_docs:
        print("\nFound relevant documents:")
        for i, doc in enumerate(relevant_docs, 1):
            print(f"  {i}. {doc['title']} (ID: {doc['doc_id']})")
            print(f"     Relevance: {doc['relevance_score']:.3f}")

        print("\nSelect document IDs (comma-separated numbers, or enter doc_ids directly):")
        selection = input("> ").strip()

        if selection:
            # Try to parse as numbers first
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                context_doc_ids = [
                    relevant_docs[i]["doc_id"]
                    for i in indices
                    if 0 <= i < len(relevant_docs)
                ]
            except ValueError:
                # Parse as direct doc_ids
                context_doc_ids = [x.strip() for x in selection.split(",")]
        else:
            # Use top result
            context_doc_ids = [relevant_docs[0]["doc_id"]]
            print(f"Using top result: {context_doc_ids[0]}")
    else:
        print("\nNo relevant documents found. Please enter document IDs manually:")
        doc_ids_input = input("Document IDs (comma-separated): ").strip()
        context_doc_ids = [x.strip() for x in doc_ids_input.split(",")] if doc_ids_input else []

    if not context_doc_ids:
        print("At least one document ID is required. Cancelled.")
        return None

    # Get metadata (optional)
    print("\nMetadata (optional, JSON format, or press Enter to skip):")
    metadata_input = input("> ").strip()
    metadata = {}
    if metadata_input:
        try:
            metadata = json.loads(metadata_input)
        except json.JSONDecodeError:
            print("Invalid JSON. Using empty metadata.")

    return BenchmarkQuestion(
        question_id=question_id,
        question=question,
        ground_truth_answer=ground_truth,
        context_doc_ids=context_doc_ids,
        metadata=metadata,
    )


def create_dataset_interactive() -> BenchmarkDataset:
    """
    Interactively create a benchmark dataset.

    Returns:
        BenchmarkDataset
    """
    print("=" * 60)
    print("Benchmark Dataset Creator")
    print("=" * 60)

    # Get dataset info
    dataset_name = input("\nDataset name (e.g., textbook_benchmark): ").strip()
    if not dataset_name:
        dataset_name = "textbook_benchmark"

    description = input("Description (optional): ").strip()
    if not description:
        description = f"Benchmark dataset: {dataset_name}"

    # List existing documents
    print("\n" + "=" * 60)
    print("Available Documents in ChromaDB")
    print("=" * 60)
    documents = list_documents()
    if documents:
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc['title']}")
            print(f"     ID: {doc['doc_id']}")
            print(f"     Source: {doc['source']}")
            print(f"     Chunks: {doc['chunk_count']}")
    else:
        print("  No documents found. Please import documents first.")
        print("  Use: python backend/test_document_processing.py")

    # Create questions
    questions = []
    print("\n" + "=" * 60)
    print("Creating Questions")
    print("=" * 60)

    while True:
        question = create_question_interactive()
        if question:
            questions.append(question)
            print(f"\n✅ Question '{question.question_id}' added. Total: {len(questions)}")

        continue_input = input("\nAdd another question? (y/n): ").strip().lower()
        if continue_input != "y":
            break

    # Create dataset
    dataset = BenchmarkDataset(
        dataset_name=dataset_name,
        description=description,
        questions=questions,
        metadata={
            "version": "1.0",
            "created_date": "2024-01-XX",
            "total_questions": len(questions),
        },
    )

    return dataset


def create_dataset_from_template() -> BenchmarkDataset:
    """
    Create a dataset from a template file.

    Returns:
        BenchmarkDataset
    """
    print("=" * 60)
    print("Create Dataset from Template")
    print("=" * 60)

    template_path = input("\nTemplate file path (JSON): ").strip()
    if not template_path:
        print("Template path is required.")
        return None

    template_file = Path(template_path)
    if not template_file.exists():
        print(f"Template file not found: {template_file}")
        return None

    with open(template_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return BenchmarkDataset(**data)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create benchmark dataset from PDF textbook"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "template"],
        default="interactive",
        help="Creation mode: interactive or template",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_data/textbook_benchmark.json",
        help="Output file path",
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Template file path (for template mode)",
    )

    args = parser.parse_args()

    # Create dataset
    if args.mode == "interactive":
        dataset = create_dataset_interactive()
    else:
        if args.template:
            template_file = Path(args.template)
            with open(template_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            dataset = BenchmarkDataset(**data)
        else:
            print("Template file required for template mode. Use --template <file>")
            return

    if not dataset or len(dataset.questions) == 0:
        print("\n⚠️  No questions created. Exiting.")
        return

    # Save dataset
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_benchmark_dataset(dataset, output_path)

    print("\n" + "=" * 60)
    print("✅ Dataset Created Successfully!")
    print("=" * 60)
    print(f"Dataset: {dataset.dataset_name}")
    print(f"Questions: {len(dataset.questions)}")
    print(f"Output: {output_path}")
    print("\nTo run evaluation:")
    print(
        f"  python -m backend.app.scripts.run_benchmark "
        f"--dataset {output_path} --collection documents --k 4"
    )


if __name__ == "__main__":
    main()

