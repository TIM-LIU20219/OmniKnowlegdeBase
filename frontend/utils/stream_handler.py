"""Stream handler for processing SSE stream responses."""

import json
import logging
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


def process_rag_stream(stream_generator) -> Iterator[str]:
    """
    Process RAG stream response and yield text chunks.

    Args:
        stream_generator: Generator from stream_rag_query

    Yields:
        Text chunks
    """
    try:
        for event in stream_generator:
            if event.get("type") == "chunk":
                yield event.get("content", "")
            elif event.get("type") == "done":
                # Final result available in event["result"]
                break
            elif event.get("type") == "error":
                error_msg = event.get("error", "Unknown error")
                logger.error(f"Stream error: {error_msg}")
                yield f"\n\nError: {error_msg}"
                break
    except Exception as e:
        logger.error(f"Error processing RAG stream: {e}")
        yield f"\n\nError: {str(e)}"


def process_agentic_stream(stream_generator) -> Iterator[dict]:
    """
    Process Agentic Search stream response and yield events.

    Args:
        stream_generator: Generator from stream_agentic_query

    Yields:
        Event dictionaries with type and data
    """
    try:
        for event in stream_generator:
            yield event
    except Exception as e:
        logger.error(f"Error processing Agentic stream: {e}")
        yield {"type": "error", "error": str(e)}

