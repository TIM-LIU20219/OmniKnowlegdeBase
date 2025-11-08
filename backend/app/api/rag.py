"""RAG Q&A API routes."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.api.schemas import (
    AgenticQueryRequest,
    AgenticQueryResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    StreamChunk,
)
from backend.app.services.agentic_rag_service import AgenticRAGService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


def _create_rag_service(
    collection: str = "documents", k: int = 4, threshold: Optional[float] = None
) -> RAGService:
    """Create RAG service instance."""
    vector_service = VectorService()
    embedding_service = EmbeddingService()
    llm_service = LLMService()

    return RAGService(
        vector_service=vector_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        collection_name=collection,
        k=k,
        score_threshold=threshold,
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """Query the RAG system with a question (synchronous)."""
    try:
        rag_service = _create_rag_service(
            collection=request.collection, k=request.k, threshold=request.threshold
        )
        result = rag_service.query(request.question)
        return RAGQueryResponse(**result)
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def stream_rag_query(request: RAGQueryRequest):
    """Stream RAG query response using Server-Sent Events (SSE)."""
    async def generate():
        try:
            rag_service = _create_rag_service(
                collection=request.collection, k=request.k, threshold=request.threshold
            )

            # First, retrieve documents to get sources
            documents = rag_service.retriever.get_relevant_documents(request.question)
            
            # Stream the answer chunks
            for chunk in rag_service.stream_query(request.question):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Send final result with sources
            result = rag_service.query(request.question)
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"

        except Exception as e:
            logger.error(f"Error in RAG stream query: {e}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/agentic-query", response_model=AgenticQueryResponse)
async def agentic_query(request: AgenticQueryRequest):
    """Query using Agentic Search with LLM tool calling (synchronous)."""
    try:
        agentic_rag_service = AgenticRAGService(
            max_iterations=request.max_iterations,
            default_strategy=request.strategy,
        )

        result = agentic_rag_service.query(
            question=request.question,
            strategy=request.strategy,
        )

        return AgenticQueryResponse(**result)
    except Exception as e:
        logger.error(f"Error in Agentic query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agentic-query/stream")
async def stream_agentic_query(request: AgenticQueryRequest):
    """Stream Agentic Search query response with tool call events (SSE)."""
    async def generate():
        try:
            agentic_rag_service = AgenticRAGService(
                max_iterations=request.max_iterations,
                default_strategy=request.strategy,
            )

            # Track tool calls and final result
            tool_calls = []
            full_answer = ""
            sources = []
            metadata = {}

            # Stream the answer chunks
            for chunk in agentic_rag_service.stream_query(
                question=request.question,
                strategy=request.strategy,
            ):
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Get final result to extract tool calls and sources
            result = agentic_rag_service.query(
                question=request.question,
                strategy=request.strategy,
            )

            # Send tool calls as events
            for tool_call in result.get("tool_calls", []):
                tool_event = {
                    "type": "tool_call",
                    "data": {
                        "iteration": tool_call.get("iteration", 0),
                        "tool_name": tool_call.get("tool_name"),
                        "tool_args": tool_call.get("tool_args", {}),
                        "result": tool_call.get("result"),
                    }
                }
                yield f"data: {json.dumps(tool_event)}\n\n"

            # Send final result
            done_event = {
                "type": "done",
                "result": {
                    "answer": result.get("answer", full_answer),
                    "sources": result.get("sources", []),
                    "tool_calls": result.get("tool_calls", []),
                    "metadata": result.get("metadata", {}),
                }
            }
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            logger.error(f"Error in Agentic stream query: {e}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/history")
async def get_query_history():
    """Get query history (placeholder - not yet implemented)."""
    return {"message": "Query history feature not yet implemented"}

