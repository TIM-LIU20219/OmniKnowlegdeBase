"""Benchmark dataset models for RAG evaluation."""

from typing import List, Optional

from pydantic import BaseModel, Field


class BenchmarkQuestion(BaseModel):
    """A single question in the benchmark dataset."""

    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="Question text")
    ground_truth_answer: str = Field(..., description="Expected answer")
    context_doc_ids: List[str] = Field(
        ..., description="List of document IDs that contain the answer"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BenchmarkDataset(BaseModel):
    """Benchmark dataset for RAG evaluation."""

    dataset_name: str = Field(..., description="Name of the dataset")
    description: str = Field(..., description="Dataset description")
    questions: List[BenchmarkQuestion] = Field(
        ..., description="List of questions to evaluate"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional dataset metadata"
    )

    def __len__(self) -> int:
        """Return number of questions in dataset."""
        return len(self.questions)

    def get_question(self, question_id: str) -> Optional[BenchmarkQuestion]:
        """
        Get question by ID.

        Args:
            question_id: Question identifier

        Returns:
            BenchmarkQuestion or None if not found
        """
        for q in self.questions:
            if q.question_id == question_id:
                return q
        return None

