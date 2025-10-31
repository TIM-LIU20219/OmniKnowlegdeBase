# OmniKnowledgeBase

A multi-functional knowledge base with document processing, Obsidian-like note management, RAG-based Q&A, and a modern web UI.

## Features

- 📄 Document processing (Markdown, PDF, URL)
- 📝 Obsidian-style note management
- 🤖 RAG-based Q&A system
- 🎨 Modern web UI

## Quick Start

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development guidelines and workflow.

## License

[Add your license here]

