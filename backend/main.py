"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import documents, notes, rag, system, vectors
from backend.app.utils.filesystem import ensure_directories

# Initialize directories on startup
ensure_directories()

app = FastAPI(
    title="OmniKnowledgeBase API",
    description="Multi-functional knowledge base API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents.router)
app.include_router(rag.router)
app.include_router(notes.router)
app.include_router(vectors.router)
app.include_router(system.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "OmniKnowledgeBase API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

