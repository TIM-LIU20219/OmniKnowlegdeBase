"""Example benchmark dataset for RAG evaluation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.models.benchmark import BenchmarkDataset, BenchmarkQuestion


def create_example_dataset() -> BenchmarkDataset:
    """
    Create an example benchmark dataset.

    Returns:
        BenchmarkDataset with example questions
    """
    questions = [
        BenchmarkQuestion(
            question_id="example_001",
            question="What is the default chunk size used in the chunking service?",
            ground_truth_answer="The default chunk size is 1000 characters.",
            context_doc_ids=[
                "chunking_service_doc",  # Expected doc_id that contains this info
            ],
            metadata={"category": "configuration", "difficulty": "easy"},
        ),
        BenchmarkQuestion(
            question_id="example_002",
            question="What embedding model is used by default?",
            ground_truth_answer="The default embedding model is all-MiniLM-L6-v2.",
            context_doc_ids=["embedding_service_doc"],
            metadata={"category": "configuration", "difficulty": "easy"},
        ),
        BenchmarkQuestion(
            question_id="example_003",
            question="How does the document service process documents?",
            ground_truth_answer="The document service processes documents by chunking text, generating embeddings, and storing chunks in the vector database.",
            context_doc_ids=["document_service_doc"],
            metadata={"category": "architecture", "difficulty": "medium"},
        ),
    ]

    dataset = BenchmarkDataset(
        dataset_name="example_rag_benchmark",
        description="Example benchmark dataset for testing RAG system",
        questions=questions,
        metadata={
            "version": "1.0",
            "created_date": "2024-01-01",
        },
    )

    return dataset


if __name__ == "__main__":
    # Create example dataset
    dataset = create_example_dataset()

    # Save to file
    output_path = Path("benchmark_data/example_dataset.json")
    from backend.app.services.benchmark_evaluator import save_benchmark_dataset

    save_benchmark_dataset(dataset, output_path)
    print(f"Created example dataset: {output_path}")

