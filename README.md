# 🧠 Personal AI Agent

A production-ready, self-hosted personal AI agent with memory, tool calling, planning, multimodal capabilities, and a stunning web interface.

---

## 🏗️ Architecture

```
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │ Next.js 14 UI   │ :3000
                  │ (TypeScript)    │
                  └────────┬────────┘
                           │ REST / SSE / WebSocket
                           ▼
                  ┌─────────────────┐
                  │ FastAPI Backend │ :8000
                  │ Agent Runtime   │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌──────────┐    ┌──────────────┐  ┌──────────────┐
   │  Ollama  │    │  PostgreSQL  │  │    Redis     │
   │ (LLMs)   │    │ + pgvector   │  │ + Celery     │
   └──────────┘    └──────────────┘  └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows)
- [Ollama](https://ollama.com/) installed locally
- Node.js 20+ (for frontend dev)
- Python 3.12+ (for backend dev)

### 1. Clone & Configure

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings (secret keys, etc.)
```

### 2. Pull Required Ollama Models

```bash
# General chat model
ollama pull llama3.2:3b

# Coding model
ollama pull qwen2.5-coder:7b

# Vision model
ollama pull llava:7b

# Embedding model
ollama pull nomic-embed-text
```

### 3. Start with Docker Compose

```bash
docker compose up -d
```

This starts:
- PostgreSQL 16 + pgvector on port 5432
- Redis 7 on port 6379
- Ollama on port 11434
- FastAPI backend on port 8000
- Celery worker
- Next.js frontend on port 3000

### 4. Open the App

Navigate to: **http://localhost:3000**

Register a new account and start chatting!

---

## 🛠️ Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker compose up postgres redis -d

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Celery Worker

```bash
cd backend
celery -A backend.workers.celery_app worker --loglevel=info
```

### Celery Beat (Scheduler)

```bash
cd backend
celery -A backend.workers.celery_app beat --loglevel=info
```

---

## 📁 Project Structure

```
personal-agent/
├── .env.example              # Environment variables template
├── docker-compose.yml        # Full stack orchestration
├── README.md
│
├── backend/                  # Python FastAPI backend
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Pydantic settings
│   ├── requirements.txt
│   │
│   ├── api/                  # HTTP API routes
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── chat.py           # Chat + streaming
│   │   ├── conversations.py  # Conversation management
│   │   ├── memory.py         # Memory CRUD
│   │   ├── tasks.py          # Task management
│   │   ├── files.py          # File upload + search
│   │   ├── tools.py          # Tool management
│   │   ├── voice.py          # STT + TTS endpoints
│   │   └── admin.py          # Admin panel
│   │
│   ├── agent/                # Core agent runtime
│   │   ├── runtime.py        # Main agent loop (ReAct)
│   │   ├── intent_router.py  # Intent classification
│   │   ├── context_manager.py# Context orchestration
│   │   ├── planner.py        # Task planning engine
│   │   ├── verifier.py       # Response verification
│   │   └── supervisor.py     # Multi-agent supervisor
│   │
│   ├── llm/                  # LLM provider abstraction
│   │   ├── gateway.py        # Unified LLM interface
│   │   ├── ollama_provider.py# Ollama implementation
│   │   └── model_router.py   # Task-based model selection
│   │
│   ├── memory/               # Memory subsystem
│   │   ├── short_term.py     # Conversation context
│   │   ├── long_term.py      # Persistent memories
│   │   ├── vector_store.py   # pgvector similarity search
│   │   ├── user_profile.py   # User model/profile
│   │   ├── knowledge_graph.py# Entity relationships
│   │   └── context_builder.py# Context assembly
│   │
│   ├── tools/                # Tool system
│   │   ├── base.py           # BaseTool interface
│   │   ├── registry.py       # Tool registry
│   │   ├── permission_manager.py  # RBAC + approvals
│   │   ├── web_search.py     # DuckDuckGo search
│   │   ├── file_ops.py       # File read/write
│   │   ├── code_runner.py    # Sandboxed execution
│   │   ├── calculator.py     # Safe math
│   │   ├── datetime_tool.py  # Date/time + reminders
│   │   ├── weather.py        # Weather (Open-Meteo)
│   │   ├── email_tool.py     # Email read/send
│   │   ├── browser_tool.py   # Web browsing (Playwright)
│   │   ├── memory_tool.py    # Remember/recall tools
│   │   └── vision_tool.py    # Image analysis tool
│   │
│   ├── planning/             # Task planning infrastructure
│   │   ├── task_manager.py   # Task lifecycle management
│   │   ├── state_manager.py  # Redis task state
│   │   └── scheduler.py      # Background task scheduling
│   │
│   ├── multimodal/           # Vision + Voice + Computer Use
│   │   ├── vision.py         # LLaVA image analysis
│   │   ├── stt.py            # Whisper speech-to-text
│   │   ├── tts.py            # Local text-to-speech
│   │   └── computer_use.py   # Sandboxed browser automation
│   │
│   ├── documents/            # Document RAG pipeline
│   │   ├── parser.py         # PDF/DOCX/XLSX/CSV parser
│   │   ├── chunker.py        # Text chunking
│   │   └── indexer.py        # Embed + store in pgvector
│   │
│   ├── security/             # Security subsystem
│   │   ├── auth.py           # JWT authentication
│   │   ├── rbac.py           # Role-based access control
│   │   ├── sandbox.py        # Code execution sandbox
│   │   ├── prompt_guard.py   # Prompt injection protection
│   │   └── audit.py          # Audit logging
│   │
│   ├── observability/        # Monitoring + logging
│   │   ├── logger.py         # Structured JSON logging
│   │   ├── tracing.py        # OpenTelemetry tracing
│   │   └── metrics.py        # Custom metrics
│   │
│   ├── evaluation/           # Agent evaluation
│   │   ├── evaluator.py      # Evaluation framework
│   │   └── test_runner.py    # Test suite
│   │
│   ├── workers/              # Background workers
│   │   ├── celery_app.py     # Celery configuration
│   │   └── tasks.py          # Celery task definitions
│   │
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── crud/                 # Database CRUD operations
│   └── database/             # DB connection + migrations
│
├── frontend/                 # Next.js 14 frontend
│   ├── app/                  # Next.js App Router pages
│   │   ├── (auth)/           # Login + Register
│   │   └── (dashboard)/      # Main app pages
│   │       ├── chat/         # Streaming chat UI
│   │       ├── tasks/        # Task tracker
│   │       ├── memory/       # Memory browser
│   │       ├── files/        # File manager
│   │       ├── tools/        # Tools panel
│   │       ├── automations/  # Scheduled tasks
│   │       └── settings/     # User settings
│   ├── components/           # Reusable UI components
│   ├── lib/                  # API client, stores, hooks
│   └── ...
│
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
│
└── docs/
    └── architecture.md
```

---

## 🤖 Features

### Core Agent Capabilities
- ✅ **Streaming chat** with Server-Sent Events
- ✅ **Intent routing** — automatically routes to the right pipeline
- ✅ **ReAct agent loop** — reason + act + observe + verify
- ✅ **Multi-step task planning** with dependency tracking
- ✅ **Task resumption** — pause, resume, cancel tasks
- ✅ **Human-in-the-loop approval** for high-risk actions

### Memory System
- ✅ **Short-term memory** — sliding context window with summarization
- ✅ **Long-term memory** — persistent facts, preferences, projects
- ✅ **Semantic search** — pgvector similarity search
- ✅ **Knowledge graph** — entity relationships
- ✅ **User profile** — structured personal information
- ✅ **Auto memory extraction** from conversations

### Tools (12+)
| Tool | Description | Risk |
|------|-------------|------|
| `search_web` | DuckDuckGo search + page fetching | Low |
| `browse_web` | Playwright browser automation | Medium |
| `read_file` | Read files from user workspace | Low |
| `write_file` | Write files to user workspace | Medium |
| `delete_file` | Delete files (approval required) | High |
| `run_code` | Sandboxed Python execution | High |
| `calculate` | Safe mathematical expressions | Low |
| `get_datetime` | Current date/time/timezone | Low |
| `set_reminder` | Create reminders/timers | Low |
| `get_weather` | Weather via Open-Meteo | Low |
| `analyze_image` | Vision analysis via LLaVA | Low |
| `remember` | Store to long-term memory | Low |
| `recall` | Search long-term memory | Low |
| `read_email` | Read emails (IMAP) | Medium |
| `send_email` | Send emails (approval required) | High |

### Multimodal
- ✅ **Vision** — Image understanding, OCR, UI analysis (LLaVA via Ollama)
- ✅ **Speech-to-text** — Faster-Whisper (local, offline)
- ✅ **Text-to-speech** — Local TTS with streaming support
- ✅ **Computer use** — Sandboxed Playwright browser automation

### Document Intelligence
- ✅ **PDF, DOCX, XLSX, CSV, TXT** parsing
- ✅ **Semantic chunking** with overlap
- ✅ **Vector indexing** via pgvector
- ✅ **Semantic search** across documents

### Security
- ✅ **JWT authentication** with refresh token rotation
- ✅ **RBAC** — role-based access control
- ✅ **Tool permissions** — per-tool, per-user access control
- ✅ **Approval system** — high-risk actions require explicit approval
- ✅ **Sandboxed code execution**
- ✅ **Prompt injection protection**
- ✅ **Comprehensive audit logging**

### Background Tasks
- ✅ **Celery + Redis** task queue
- ✅ **Cron scheduling** — recurring agent tasks
- ✅ **One-time scheduled tasks**
- ✅ **Task state persistence** in Redis

### Observability
- ✅ **OpenTelemetry** distributed tracing
- ✅ **Structured JSON logging** via structlog
- ✅ **Custom metrics** (token count, tool latency, etc.)
- ✅ **Agent evaluation harness** with test suites

### Multi-Agent
- ✅ **Supervisor + Specialists** — Researcher, Coder, Planner agents
- ✅ **Automatic delegation** for complex tasks
- ✅ **Result aggregation**

---

## 🔧 Configuration

All configuration is done via `.env`:

```bash
# Core models
OLLAMA_CHAT_MODEL=llama3.2:3b        # Change to llama3.1:8b for better quality
OLLAMA_CODE_MODEL=qwen2.5-coder:7b
OLLAMA_VISION_MODEL=llava:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Security (CHANGE THESE!)
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

---

## 🧪 Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires running backend)
pytest tests/integration/ -v

# Agent evaluation suite
pytest tests/evaluation/ -v

# All tests
pytest tests/ -v --tb=short
```

---

## 📊 API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🚀 Production Deployment

See [docs/architecture.md](docs/architecture.md) for production deployment guide including:
- Docker Swarm setup
- Nginx reverse proxy
- SSL/TLS with Let's Encrypt
- Monitoring with Prometheus + Grafana
- Backup strategy for PostgreSQL

---

## 📋 Roadmap

### Phase 1 (Complete) ✅
- Local LLM + basic chat
- Streaming + conversations + PostgreSQL
- Context manager + memory
- Intent router + model routing

### Phase 2 (Complete) ✅
- Tool calling + permissions
- Planning + task execution
- RAG + files + web research
- Background tasks + automation

### Phase 3 (Complete) ✅
- Vision + voice + computer use
- Security + evaluation + observability

### Phase 4 (Future)
- Mobile app (React Native)
- Smart-home integration
- Calendar and email automation
- Custom model fine-tuning

---

## 🤝 Contributing

This is a personal agent project. Feel free to fork and customize for your own needs.

---

## ⚠️ Security Notice

This agent can execute code, access files, browse the web, and send emails. Always:
1. Review tool permissions carefully
2. Use the approval system for high-risk actions
3. Keep your `.env` file secret
4. Never expose the backend to the public internet without proper authentication
