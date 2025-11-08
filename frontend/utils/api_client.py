"""FastAPI client wrapper for Streamlit frontend."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from frontend.config import API_BASE_URL

logger = logging.getLogger(__name__)


class APIClient:
    """Client for making requests to FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the FastAPI backend
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: JSON data for request body
            files: Files for multipart/form-data
            params: Query parameters

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if files:
                response = self.client.request(
                    method, url, files=files, data=json_data, params=params
                )
            else:
                response = self.client.request(
                    method, url, json=json_data, params=params
                )

            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    # Document API methods
    def create_document(
        self,
        pdf_file: Optional[bytes] = None,
        markdown_file: Optional[bytes] = None,
        filename: Optional[str] = None,
        url: Optional[str] = None,
        skip_duplicates: bool = True,
        import_batch: Optional[str] = None,
    ) -> Dict:
        """Create a document."""
        files = {}
        data = {}

        if pdf_file:
            files["pdf_file"] = (filename or "document.pdf", pdf_file, "application/pdf")
        elif markdown_file:
            files["markdown_file"] = (filename or "document.md", markdown_file, "text/markdown")
        elif url:
            data["url"] = url

        data["skip_duplicates"] = skip_duplicates
        if import_batch:
            data["import_batch"] = import_batch

        url_endpoint = f"{self.base_url}/api/documents"
        
        try:
            if files:
                response = self.client.post(url_endpoint, files=files, data=data)
            else:
                response = self.client.post(url_endpoint, data=data)
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    def list_documents(self, by_batch: Optional[str] = None) -> Dict:
        """List all documents."""
        params = {}
        if by_batch:
            params["by_batch"] = by_batch
        return self._request("GET", "/api/documents", params=params)

    def get_document(self, doc_id: str) -> Dict:
        """Get document details."""
        return self._request("GET", f"/api/documents/{doc_id}")

    def delete_document(self, doc_id: str) -> None:
        """Delete a document."""
        self._request("DELETE", f"/api/documents/{doc_id}")

    def get_document_chunks(self, doc_id: str) -> List[Dict]:
        """Get document chunks."""
        return self._request("GET", f"/api/documents/{doc_id}/chunks")

    def search_documents(
        self, query: str, k: int = 5, show_source_info: bool = False
    ) -> List[Dict]:
        """Search documents."""
        return self._request(
            "POST",
            "/api/documents/search",
            json_data={"query": query, "k": k, "show_source_info": show_source_info},
        )

    def find_duplicates(self) -> Dict:
        """Find duplicate documents."""
        return self._request("GET", "/api/documents/duplicates")

    # RAG API methods
    def query_rag(
        self, question: str, collection: str = "documents", k: int = 4, threshold: Optional[float] = None
    ) -> Dict:
        """Query RAG system."""
        return self._request(
            "POST",
            "/api/rag/query",
            json_data={
                "question": question,
                "collection": collection,
                "k": k,
                "threshold": threshold,
            },
        )

    def stream_rag_query(
        self, question: str, collection: str = "documents", k: int = 4, threshold: Optional[float] = None
    ):
        """Stream RAG query response."""
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/rag/query/stream",
            json={
                "question": question,
                "collection": collection,
                "k": k,
                "threshold": threshold,
            },
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    import json
                    data = json.loads(line[6:])
                    yield data

    def agentic_query(
        self,
        question: str,
        strategy: str = "hybrid",
        max_iterations: int = 5,
    ) -> Dict:
        """Query Agentic Search."""
        return self._request(
            "POST",
            "/api/rag/agentic-query",
            json_data={
                "question": question,
                "strategy": strategy,
                "max_iterations": max_iterations,
            },
        )

    def stream_agentic_query(
        self,
        question: str,
        strategy: str = "hybrid",
        max_iterations: int = 5,
    ):
        """Stream Agentic Search query response."""
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/rag/agentic-query/stream",
            json={
                "question": question,
                "strategy": strategy,
                "max_iterations": max_iterations,
            },
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    import json
                    data = json.loads(line[6:])
                    yield data

    # Note API methods
    def create_note(
        self, title: str, content: str, file_path: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> Dict:
        """Create a note."""
        return self._request(
            "POST",
            "/api/notes",
            json_data={"title": title, "content": content, "file_path": file_path, "tags": tags},
        )

    def list_notes(self, subdirectory: Optional[str] = None) -> List[str]:
        """List all notes."""
        params = {}
        if subdirectory:
            params["subdirectory"] = subdirectory
        return self._request("GET", "/api/notes", params=params)

    def get_note(self, file_path: str) -> Dict:
        """Get note content."""
        return self._request("GET", f"/api/notes/{file_path}")

    def update_note(
        self,
        file_path: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """Update a note."""
        return self._request(
            "PUT",
            f"/api/notes/{file_path}",
            json_data={"content": content, "title": title, "tags": tags},
        )

    def delete_note(self, file_path: str) -> None:
        """Delete a note."""
        self._request("DELETE", f"/api/notes/{file_path}")

    def search_notes(
        self, query: Optional[str] = None, tag: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """Search notes."""
        return self._request(
            "POST",
            "/api/notes/search",
            json_data={"query": query, "tag": tag, "limit": limit},
        )

    # Vector API methods
    def list_collections(self) -> List[str]:
        """List all collections."""
        return self._request("GET", "/api/vectors/collections")

    def get_collection_stats(self, name: str) -> Dict:
        """Get collection statistics."""
        return self._request("GET", f"/api/vectors/collections/{name}/stats")

    def query_collection(self, name: str, query_text: str, k: int = 5) -> List[Dict]:
        """Query a collection."""
        return self._request(
            "POST",
            f"/api/vectors/collections/{name}/query",
            json_data={"query_text": query_text, "k": k},
        )

    # System API methods
    def get_system_stats(self) -> Dict:
        """Get system statistics."""
        return self._request("GET", "/api/system/stats")

    def health_check(self) -> Dict:
        """Health check."""
        return self._request("GET", "/api/system/health")

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# Global client instance
_client: Optional[APIClient] = None


def get_client() -> APIClient:
    """Get or create global API client instance."""
    global _client
    if _client is None:
        _client = APIClient()
    return _client

