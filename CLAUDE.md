# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

<<<<<<< HEAD
DragonAI is an intelligent AI assistant platform built with FastAPI and LangChain/LangGraph. It features multi-agent task dispatching, RAG knowledge base, tool calling (web search, code execution, image generation), and long-term memory storage.

## Tech Stack

- **Backend**: FastAPI + Uvicorn, SQLAlchemy 2.0 (async), PostgreSQL, Redis, ChromaDB
- **AI Framework**: LangChain + LangGraph + DeepAgents for agent orchestration
- **LLM**: DashScope (Tongyi Qwen series via Alibaba Cloud)
- **Frontend**: Vue 3 + TypeScript + Vite + Pinia + Element Plus
- **Database Migration**: Alembic
- **Testing**: pytest with asyncio support
- **Deployment**: Docker Compose with Nginx reverse proxy

## Common Commands

### Development

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with required API keys (QWEN_API_KEY, TAVILY_API_KEY)

# Database migrations
alembic upgrade head          # Run all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Initialize database tables (without migrations)
python scripts/init_db.py

# Start development server
python run.py
# Or directly with uvicorn
uvicorn app.main:create_app --reload --factory
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_chat_service.py -v

# Run integration tests only
pytest tests/integration/ -v

# Run unit tests only
pytest tests/unit/ -v
```

### Frontend
=======
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
>>>>>>> 74a94b8ef5d80e3ffc0533ac0ed46e39f96b2a5e

```bash
cd frontend
npm install
<<<<<<< HEAD
npm run dev      # Development server
npm run build    # Production build
```

### Production Deployment

```bash
# Using deploy script
chmod +x deploy.sh
./deploy.sh deploy    # Full deploy (build + start)
./deploy.sh build     # Build only
./deploy.sh logs      # View logs
./deploy.sh stop      # Stop services
./deploy.sh restart   # Restart services
./deploy.sh status    # Check container status

# Manual Docker commands
docker-compose up -d
docker-compose logs -f backend
docker-compose down
=======
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
>>>>>>> 74a94b8ef5d80e3ffc0533ac0ed46e39f96b2a5e
```

## Architecture Overview

<<<<<<< HEAD
### Application Structure

```
app/
├── api/v1/           # API routers (auth, chat, conversations, files, knowledge, tools)
├── agents/           # AgentFactory - creates DeepAgents with task dispatching
├── cache/            # Redis client and cache warmup
├── core/             # Database, security, rate limiting, logging config
├── llm/              # DashScope client wrapper for Tongyi models
├── models/           # SQLAlchemy ORM models (User, Conversation, Message)
├── rag/              # RAG pipeline: hybrid retriever, reranker, document loader
├── schemas/          # Pydantic request/response models
├── services/         # Business logic layer
├── storage/          # File storage, vector store, sandbox
└── tools/            # Agent tools: web_search, code_tools, image_tools, rag_tool
```

### Key Architectural Patterns

**Agent System (app/agents/agent_factory.py)**
- Uses DeepAgents library with `create_deep_agent()`
- Main agent handles task dispatching to sub-agents
- Sub-agents: general-purpose, researcher, coder, image-creator
- Long-term memory via CompositeBackend routing to PostgreSQL
- Checkpointer for conversation state (AsyncPostgresSaver)

**Database (app/core/database.py)**
- Async SQLAlchemy with asyncpg driver
- Converts `postgresql://` URLs to `postgresql+asyncpg://`
- Pool size: 20, max overflow: 40
- Dependency injection via `get_db()` generator

**LLM Integration (app/llm/dashscope_client.py)**
- Unified DashScope SDK client for all Tongyi models
- Supports both Generation (text) and MultiModalConversation APIs
- Async wrapper using `asyncio.to_thread()`

**RAG Pipeline (app/rag/)**
- Hybrid retriever: vector + BM25 with configurable alpha
- Reranker: Cross-encoder or Cohere
- Document processing with unstructured library
- ChromaDB for vector storage

**Streaming (app/services/stream/)**
- SSE with heartbeat for long-running agent tasks
- StreamProcessor for chunked responses

### Configuration

Environment variables managed in `app/config.py` via Pydantic Settings:

Required:
- `QWEN_API_KEY` - DashScope API key for LLM
- `TAVILY_API_KEY` - Web search API key
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key

Model Configuration:
- General: `deepseek-v3.1` (fast), `qwen-plus-2025-12-01` (expert)
- Vision: `qwen-vl-ocr`, `qwen3-vl-plus`
- Image: `qwen-image`, `qwen-image-plus`
- Coder: `qwen3-coder-flash`, `qwen3-coder-plus`
- Embedding: `text-embedding-v4`

### Testing Structure

- `tests/conftest.py` - Shared fixtures with SQLite in-memory for unit tests
- `tests/unit/` - Isolated unit tests with mocked dependencies
- `tests/integration/` - API integration tests requiring real services

### Important Notes

- Windows requires `WindowsSelectorEventLoopPolicy` (configured in `run.py`)
- Database URLs automatically converted to asyncpg format
- Agent warmup runs on startup to cache model connections
- Rate limiting uses Redis with slowapi
- File uploads use signature verification for security
- Storage directory used for files, skills, and sandbox
=======
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
>>>>>>> 74a94b8ef5d80e3ffc0533ac0ed46e39f96b2a5e
