# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DragonAI is a Chinese AI assistant platform built with FastAPI (backend) and Vue 3 + TypeScript (frontend). It integrates with Tongyi Qianwen (Qwen) models via LangChain/LangGraph and supports features like multi-turn conversations, tool calling, RAG knowledge base, and streaming responses via SSE.

**Tech Stack:**
- Backend: FastAPI, LangChain/LangGraph, SQLAlchemy (async), PostgreSQL, Redis, ChromaDB
- Frontend: Vue 3, TypeScript, Vite, Pinia, Element Plus
- AI: Tongyi Qianwen (Qwen) models via DashScope API

## Common Commands

### Backend Development

```bash
# Setup (Windows compatible)
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run backend (use run.py for Windows compatibility)
python run.py
# OR directly with uvicorn
uvicorn app.main:create_app --factory --reload

# Run tests
pytest                    # All tests
pytest tests/unit/       # Unit tests only
pytest tests/integration/ # Integration tests only
pytest --cov=app tests/  # With coverage

# Database migrations
alembic upgrade head                    # Run pending migrations
alembic revision --autogenerate -m "description"  # Create new migration
alembic downgrade -1                    # Rollback one migration
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev      # Development server (port 5173)
npm run build    # Production build
npm run preview  # Preview production build
```

### Docker Deployment

```bash
# Full stack deployment
docker-compose up -d
docker-compose logs -f backend

# Individual services
docker-compose up -d postgres redis
docker-compose up -d backend
docker-compose up -d nginx
```

## Architecture Overview

### Backend Structure (`app/`)

**Core Components:**
- `main.py` - FastAPI app factory with lifespan management (agent warmup, Redis, cache)
- `config.py` - Pydantic-settings configuration with environment variable support
- `core/database.py` - Async SQLAlchemy setup with asyncpg

**API Layer (`api/`):**
- `v1/` - API routers: auth, chat, conversations, files, knowledge, tools, models, monitoring
- `middleware/` - Rate limiting, request size limiting, tracing
- `dependencies.py` - FastAPI dependencies (DB session, current user)

**Agent System (`agents/`):**
- `agent_factory.py` - LangChain agent creation with PostgreSQL checkpointer (AsyncPostgresSaver) or InMemorySaver fallback
- Uses `deepagents` library with SkillsMiddleware for skill-based workflows

**LLM Integration (`llm/`):**
- `model_factory.py` - Unified interface for Qwen models via ModelFactory
- `qwen_models.py` - Qwen-specific implementations (dialogue, vision, code, translation, image generation)

**RAG System (`rag/`):**
- `vector_store.py` - ChromaDB vector storage
- `hybrid_retriever.py` - BM25 + vector hybrid search (optional)
- `reranker.py` - Cross-encoder reranking (optional)
- `loader.py` - Document loaders (PDF, DOCX, etc.)

**Tools (`tools/`):**
- Code execution, file operations, web search (Tavily), image processing, RAG queries
- `ALL_TOOLS` exported for agent use

**Services (`services/`):**
- Business logic layer: chat_service, conversation_service, knowledge_service, user_service
- `repositories/` - Data access layer
- `stream/` - SSE streaming infrastructure (emitter, heartbeat, processor)

**Security (`security/`):**
- JWT authentication with token blacklist (Redis-backed)
- File signature validation

### Frontend Structure (`frontend/src/`)

- `components/` - Vue components (chat, knowledge base, etc.)
- `views/` - Page views
- `stores/` - Pinia state management
- `router/` - Vue Router configuration
- Vite dev server proxies `/api` to `http://localhost:8000`

### Database Models (`app/models/`)

- `user.py` - User accounts with password hashing
- `conversation.py` - Chat sessions
- `message.py` - Chat messages with JSON metadata

### Key Design Patterns

1. **Agent Checkpointer:** Uses LangGraph's AsyncPostgresSaver for persistence, falls back to InMemorySaver if DB unavailable
2. **Cache Warmup:** Agent and cache warmup run during startup lifespan
3. **Streaming:** SSE with heartbeat keepalive for real-time chat responses
4. **Rate Limiting:** Redis-backed with different limits per endpoint (auth: 10/min, chat: 30/min, default: 100/min)
5. **Model Selection:** Multiple Qwen models configured for different tasks (fast vs expert modes)

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required:**
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - JWT signing key
- `QWEN_API_KEY` - DashScope API key

**Optional:**
- `REDIS_URL` - Redis connection (default: localhost:6379/0)
- `TAVILY_API_KEY` - Web search capability
- `LANGSMITH_TRACING` - Enable LangSmith tracing

## Testing

- `pytest.ini` configured for asyncio mode
- Unit tests in `tests/unit/`, integration in `tests/integration/`
- Use `pytest --cov=app` for coverage reports
- Mock external services (LLM APIs) in unit tests

## Windows Development Notes

- `run.py` sets `WindowsSelectorEventLoopPolicy` for psycopg compatibility
- Always use `python run.py` instead of direct uvicorn on Windows
- Use PowerShell: `.venv\Scripts\Activate.ps1`
