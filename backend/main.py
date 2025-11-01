"""Main FastAPI application entry point."""

from fastapi import FastAPI

from backend.app.utils.filesystem import ensure_directories

# Initialize directories on startup
ensure_directories()

app = FastAPI(
    title="OmniKnowledgeBase API",
    description="Multi-functional knowledge base API",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "OmniKnowledgeBase API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

