# Streamlit Frontend for OmniKnowledgeBase

This is the Streamlit frontend application for OmniKnowledgeBase, providing a web interface for document management, RAG queries, and Agentic Search.

## Setup

1. Install dependencies:
```bash
pip install streamlit httpx python-dotenv pandas
```

2. Configure API URL (optional):
Create a `.env` file in the `frontend` directory:
```
API_BASE_URL=http://localhost:8000
```

## Running the Application

1. Start the FastAPI backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. Start the Streamlit frontend:
```bash
cd frontend
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Pages

- **Dashboard**: System overview and statistics
- **Documents**: Upload and manage documents (PDF, Markdown, URL)
- **Notes**: Create and manage Obsidian-style notes
- **RAG Query**: Query documents using RAG with streaming support
- **Agentic Search**: Advanced agentic search with tool calling visualization
- **Vector Store**: Explore vector collections and test queries

## Features

- **Streaming Responses**: Real-time streaming of LLM responses using Server-Sent Events (SSE)
- **Tool Call Visualization**: See how Agentic Search uses tools to retrieve information
- **Document Management**: Upload, search, and manage documents
- **Note Management**: Create and edit Obsidian-style notes with link visualization
- **Vector Store Exploration**: Query and explore vector collections

