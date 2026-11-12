# 🚀 Production-Ready AI Chat API (FastAPI + SQLAlchemy 2.0 + Ollama)

A modern, asynchronous, and modular RESTful backend for conversational AI applications. Built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, and **Ollama**, featuring JWT authentication, persistent chat history, context-aware memory injection, and real-time token streaming.

---

## ✨ Key Engineering Features

- **🔐 Robust Security & JWT Auth:** Standard OAuth2 password flow (`OAuth2PasswordBearer`), password hashing with `bcrypt`, and protected route dependencies.
- **🧠 Conversational Context Memory:** Automatically retrieves the user's recent chat history from the database and injects it into the LLM prompt for stateful, context-aware conversations.
- **🌊 Real-Time HTTP Streaming:** Token-by-token streaming responses (`StreamingResponse` & Async Generators) using `httpx` and `NDJSON` parsing, with background database persistence upon stream completion.
- **⚡ 100% Asynchronous ORM:** Powered by **SQLAlchemy 2.0** (`AsyncSession`, `Mapped`, `mapped_column`) and PostgreSQL for non-blocking database operations.
- **🏗️ Clean & Modular Architecture:** Follows the standard Python `src-layout` with decoupled `APIRouter` modules (`auth`, `chat`) and centralized dependency injection (`Annotated`).
- **🧪 Automated Testing Suite:** Fast unit and integration tests using `pytest`, `pytest-asyncio`, FastAPI `dependency_overrides`, and LLM `monkeypatch` mocking.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.10+) |
| **Database & ORM** | PostgreSQL + SQLAlchemy 2.0 (Async) |
| **Data Validation** | Pydantic v2 (`pydantic-settings`) |
| **Authentication** | PyJWT + Passlib (`bcrypt`) |
| **AI / LLM Engine** | Ollama (Local LLM via `httpx` AsyncClient) |
| **Package Manager** | `uv` |
| **Testing** | `pytest` + `pytest-asyncio` |

---

## 📂 Project Architecture (`src-layout`)

```text
ai-template/
├── src/
│   └── ai_template/
│       ├── routers/
│       │   ├── auth.py          # Auth & User profile endpoints (/signup, /login, /users/me)
│       │   └── chat.py          # AI Chat, Streaming & History CRUD endpoints
│       ├── config.py            # Environment variables validation (Pydantic Settings)
│       ├── database.py          # AsyncEngine & AsyncSessionLocal setup
│       ├── dependencies.py      # Shared dependencies (DBDep, CurrentUserDep, OAuthFormDep)
│       ├── llm.py               # Async Ollama client (Standard & Streaming generators)
│       ├── main.py              # FastAPI app initialization, lifespan & router registration
│       ├── models.py            # SQLAlchemy 2.0 Declarative models (User, ChatMessage)
│       ├── schemas.py           # Pydantic v2 Request/Response schemas
│       └── security.py          # Password hashing & JWT token generation
├── tests/
│   └── test_api.py              # Automated pytest suite with mocked LLM & DB
├── pyproject.toml               # Project metadata & dependencies
└── README.md