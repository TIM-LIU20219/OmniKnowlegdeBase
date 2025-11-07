"""Script to run RAG benchmark evaluation."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.models.benchmark import BenchmarkDataset
from backend.app.services.benchmark_evaluator import (
    RAGBenchmarkEvaluator,
    load_benchmark_dataset,
)
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    """Run RAG benchmark evaluation."""
    parser = argparse.ArgumentParser(
        description="Run RAG benchmark evaluation"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to benchmark dataset JSON file",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=4,
        help="Number of documents to retrieve (default: 4)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Maximum number of questions to evaluate (default: all)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file path for results (default: benchmark_results.json)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    logger.info("Starting RAG benchmark evaluation")

    # Load dataset
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        return

    dataset = load_benchmark_dataset(dataset_path)
    logger.info(f"Loaded dataset: {dataset.dataset_name} ({len(dataset)} questions)")

    # Initialize services
    logger.info("Initializing services...")
    vector_service = VectorService()
    embedding_service = EmbeddingService()
    llm_service = LLMService()

    # Create RAG service
    rag_service = RAGService(
        vector_service=vector_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        collection_name=args.collection,
        k=args.k,
    )

    # Create evaluator
    evaluator = RAGBenchmarkEvaluator(rag_service=rag_service, dataset=dataset)

    # Run evaluation
    logger.info("Running evaluation...")
    results = evaluator.evaluate(max_questions=args.max_questions)

    # Save results
    output_path = Path(args.output)
    evaluator.save_results(output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Dataset: {results['dataset_name']}")
    print(f"Total Questions: {results['total_questions']}")
    print("\nRetrieval Metrics:")
    retrieval = results["summary"]["retrieval_metrics"]
    print(f"  Precision: {retrieval['mean_precision']:.3f}")
    print(f"  Recall: {retrieval['mean_recall']:.3f}")
    print(f"  F1: {retrieval['mean_f1']:.3f}")
    print("\nAnswer Metrics:")
    answer = results["summary"]["answer_metrics"]
    print(f"  Similarity: {answer['mean_similarity']:.3f}")
    print(f"  Mean Length: {answer['mean_answer_length']:.1f}")
    print("\nContext Metrics:")
    context = results["summary"]["context_metrics"]
    print(f"  Mean Context Length: {context['mean_context_length']:.1f}")
    print(f"  Mean Retrieval Count: {context['mean_retrieval_count']:.1f}")
    print("=" * 60)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()

