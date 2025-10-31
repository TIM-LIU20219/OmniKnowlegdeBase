# Development Guide

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Git

### Python Virtual Environment

#### Main Repository

For the main repository, use the virtual environment in `backend/venv/`:

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Unix/Mac
source venv/bin/activate

pip install -r ../requirements.txt
```

#### Worktrees

For worktree branches, you have two options:

**Option 1: Shared External Virtual Environment (Recommended)**

Create a shared virtual environment outside the repository:

```bash
# Create shared venv
python -m venv ~/.venvs/OmniKnowledgeBase

# Activate it
# On Windows
~/.venvs/OmniKnowledgeBase/Scripts/activate

# On Unix/Mac
source ~/.venvs/OmniKnowledgeBase/bin/activate

# Set environment variable
export OMNIKB_VENV_PATH=~/.venvs/OmniKnowledgeBase

# Install dependencies
pip install -r requirements.txt
```

**Option 2: Worktree-Specific Virtual Environment**

Create a separate virtual environment in each worktree:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r ../requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
# or
yarn install
```

## Development Workflow

### Running the Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

### Running the Frontend

```bash
cd frontend
npm run dev
# or
yarn dev
```

### Running Tests

```bash
# Python tests
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Python
black .

# Frontend
cd frontend
npm run format
# or
prettier --write .
```

### Linting

```bash
# Python
ruff check .

# Frontend
cd frontend
npm run lint
```

## Project Structure

```
OmniKnowledgeBase/
├── backend/              # Python backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── models/      # Database models
│   │   └── utils/       # Utility functions
│   ├── tests/           # Backend tests
│   ├── venv/            # Virtual environment (not committed)
│   └── main.py          # FastAPI application entry
├── frontend/            # TypeScript/React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/      # Custom hooks
│   │   ├── utils/      # Utilities
│   │   └── types/      # TypeScript types
│   └── public/         # Static assets
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── .prettierrc
├── .eslintrc.json
└── DEVELOPMENT.md
```

## Git Workflow

### Branching

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/<feature-name>`: Feature branches
- `worktree/<agent-id>/<feature-name>`: Worktree branches for parallel development

### Commit Messages

Follow conventional commits format:
- `feat: add document processor for PDF parsing`
- `fix: resolve vector store connection issue`
- `docs: update API documentation`
- `refactor: simplify note manager service`
- `test: add RAG service unit tests`
- `chore: update dependencies`

## Before Committing

1. Run formatters (Black, Prettier)
2. Run linters (ruff, ESLint)
3. Run tests
4. Check file lengths (300/400 line limit)
5. Verify no sensitive data in commits
6. Write clear commit message

