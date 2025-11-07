"""Create initial benchmark dataset for Foundation of LLMs textbook."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.models.benchmark import BenchmarkDataset, BenchmarkQuestion
from backend.app.services.vector_service import VectorService


def get_recent_pdf_documents():
    """Get the 6 recently imported PDF documents."""
    vector_service = VectorService()
    collection = vector_service.get_documents_collection()
    
    # Get all documents
    results = collection.get(include=["metadatas"])
    
    if not results or not results.get("ids"):
        return []
    
    # Group by doc_id
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
                "created_at": metadata.get("created_at", ""),
            }
        if doc_id:
            doc_map[doc_id]["chunk_count"] += 1
    
    # Filter PDFs with > 20 chunks and sort by created_at
    pdf_docs = [
        doc for doc in doc_map.values()
        if doc["source"] == "pdf" and doc["chunk_count"] > 20
    ]
    pdf_docs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return pdf_docs[:6]  # Get the 6 most recent


def create_initial_benchmark():
    """Create initial benchmark dataset."""
    print("Creating initial benchmark dataset for Foundation of LLMs...")
    
    # Get PDF documents
    pdf_docs = get_recent_pdf_documents()
    
    if len(pdf_docs) < 6:
        print(f"Warning: Found only {len(pdf_docs)} PDF documents. Expected 6.")
    
    print("\nFound PDF documents:")
    for i, doc in enumerate(pdf_docs, 1):
        print(f"  {i}. {doc['title']} (ID: {doc['doc_id']}, Chunks: {doc['chunk_count']})")
    
    # Map chapter numbers to doc_ids (assuming order is correct)
    chapter_docs = {}
    for i, doc in enumerate(pdf_docs[:6], 1):
        chapter_docs[i] = doc["doc_id"]
    
    # Create questions based on chapter topics
    questions = [
        BenchmarkQuestion(
            question_id="foundation_llm_001",
            question="什么是语言模型？语言模型的基本原理是什么？",
            ground_truth_answer="语言模型是一种概率模型，用于预测给定上下文的下一个词或字符的概率分布。语言模型的基本原理是通过学习大量文本数据，建立词汇序列的概率分布，从而能够预测和生成文本。",
            context_doc_ids=[chapter_docs.get(1, pdf_docs[0]["doc_id"])],
            metadata={"category": "factual", "difficulty": "easy", "chapter": "1"}
        ),
        BenchmarkQuestion(
            question_id="foundation_llm_002",
            question="大语言模型的架构有哪些主要类型？",
            ground_truth_answer="大语言模型的主要架构类型包括Transformer架构、GPT系列（生成式预训练模型）、BERT系列（双向编码器表示）、T5（文本到文本转换模型）等。",
            context_doc_ids=[chapter_docs.get(2, pdf_docs[1]["doc_id"])],
            metadata={"category": "factual", "difficulty": "medium", "chapter": "2"}
        ),
        BenchmarkQuestion(
            question_id="foundation_llm_003",
            question="什么是Prompt工程？Prompt工程的主要技术有哪些？",
            ground_truth_answer="Prompt工程是指设计和优化输入提示词（prompt）以引导大语言模型生成期望输出的技术。主要技术包括few-shot learning、chain-of-thought prompting、role prompting等。",
            context_doc_ids=[chapter_docs.get(3, pdf_docs[2]["doc_id"])],
            metadata={"category": "factual", "difficulty": "medium", "chapter": "3"}
        ),
        BenchmarkQuestion(
            question_id="foundation_llm_004",
            question="参数高效微调（PEFT）有哪些方法？",
            ground_truth_answer="参数高效微调的主要方法包括LoRA（Low-Rank Adaptation）、Adapter、Prefix Tuning、P-Tuning等，这些方法只训练模型的一小部分参数，从而降低计算成本和存储需求。",
            context_doc_ids=[chapter_docs.get(4, pdf_docs[3]["doc_id"])],
            metadata={"category": "factual", "difficulty": "medium", "chapter": "4"}
        ),
        BenchmarkQuestion(
            question_id="foundation_llm_005",
            question="什么是模型编辑？模型编辑的主要方法有哪些？",
            ground_truth_answer="模型编辑是指在不重新训练整个模型的情况下，修改模型对特定事实或知识的记忆。主要方法包括直接参数修改、知识注入、记忆更新等。",
            context_doc_ids=[chapter_docs.get(5, pdf_docs[4]["doc_id"])],
            metadata={"category": "factual", "difficulty": "hard", "chapter": "5"}
        ),
        BenchmarkQuestion(
            question_id="foundation_llm_006",
            question="什么是检索增强生成（RAG）？RAG的工作原理是什么？",
            ground_truth_answer="检索增强生成（RAG）是一种结合信息检索和文本生成的技术。RAG的工作原理是：首先从知识库中检索与查询相关的文档片段，然后将这些片段作为上下文输入到语言模型中，生成基于检索内容的答案。",
            context_doc_ids=[chapter_docs.get(6, pdf_docs[5]["doc_id"])],
            metadata={"category": "factual", "difficulty": "medium", "chapter": "6"}
        ),
    ]
    
    # Create dataset
    dataset = BenchmarkDataset(
        dataset_name="foundation_llms_benchmark",
        description="Initial benchmark dataset based on Foundation of LLMs textbook (6 chapters)",
        questions=questions,
        metadata={
            "version": "1.0",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "total_questions": len(questions),
            "source": "Foundation of LLMs textbook",
            "chapters": list(chapter_docs.keys()),
        }
    )
    
    return dataset


def main():
    """Main entry point."""
    dataset = create_initial_benchmark()
    
    # Save dataset
    output_path = Path("benchmark_data/foundation_llms_benchmark.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save dataset as JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset.model_dump(), f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Benchmark Dataset Created Successfully!")
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

