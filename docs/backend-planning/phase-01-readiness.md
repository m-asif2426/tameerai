# TameerAI — Phase 01 Readiness Checklist & Execution Guide

**Project:** TameerAI — AI Construction Compliance and Cost Intelligence  
**Target Milestone:** Phase 01 — Core Foundation, Database, & Authentication  
**Status:** Ready for User Approval (Do NOT implement until approved)  

---

## 1. Phase 01 Objective

Build the enterprise-grade foundation for the TameerAI backend without modifying the frontend. This includes:
1. Resolving the Python environment divergence (consolidating onto Python 3.12).
2. Setting up PostgreSQL 16 with `pgvector`.
3. Creating the asynchronous SQLAlchemy 2.0 ORM base and Alembic migrations.
4. Implementing the User entity, password hashing (bcrypt), and JWT authentication.
5. Providing `/api/v1/auth/register`, `/api/v1/auth/login`, and `/api/v1/auth/me` endpoints matching the frontend's expected authentication flow.

---

## 2. Environment Prerequisites

### 2.1 Python Environment Consolidation
- **Observed Issue:** There are currently two virtual environments in the workspace:
  - `tameerai/venv` (Python 3.14.6 - has only pip)
  - `tameerai/backend/venv` (Python 3.12.10 - has FastAPI 0.143.0 and Pydantic 2.14.1)
- **Recommendation:** Use `tameerai/backend/venv` (Python 3.12.10) as the standardized project virtual environment. Python 3.12 has complete pre-built wheel compatibility for all required packages (`asyncpg`, `pydantic-core`, `greenlet`, `bcrypt`, `pgvector`).

### 2.2 PostgreSQL & pgvector Installation
- PostgreSQL 16 must be running locally or via Docker.
- Required Database: `tameerai`
- Required Extension: `CREATE EXTENSION IF NOT EXISTS vector;`

---

## 3. Required Package Dependencies for Phase 01

To be placed in `tameerai/backend/requirements.txt`:
```txt
# FastAPI & ASGI Server
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1

# Database & Migrations
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
greenlet==3.1.1
pgvector==0.3.6

# Security & Authentication
passlib[bcrypt]==1.7.4
bcrypt==4.2.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.20

# HTTP & Testing
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.2
```

---

## 4. Configuration Schema (`.env`)

A `.env.example` file will be created in `tameerai/backend/.env.example`:
```env
# Application
PROJECT_NAME="TameerAI Backend"
API_V1_STR="/api/v1"
SECRET_KEY="generate_a_secure_random_secret_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# PostgreSQL Database
POSTGRES_SERVER="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_postgres_password"
POSTGRES_DB="tameerai"

# CORS Origins (allow Next.js frontend)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# LLM Providers (for Phase 03/04)
GEMINI_API_KEY="your_gemini_api_key"
```

---

## 5. File Creation Inventory for Phase 01

| File Path | Purpose |
| :--- | :--- |
| `tameerai/backend/requirements.txt` | Pinned dependency list |
| `tameerai/backend/.env.example` | Environment variable template |
| `tameerai/backend/alembic.ini` | Alembic migration configuration |
| `tameerai/backend/alembic/env.py` | Asynchronous migration runner for SQLAlchemy |
| `tameerai/backend/app/core/config.py` | Pydantic Settings class reading `.env` |
| `tameerai/backend/app/core/database.py` | Async engine (`create_async_engine`) and session factory |
| `tameerai/backend/app/core/security.py` | `get_password_hash`, `verify_password`, `create_access_token` |
| `tameerai/backend/app/core/deps.py` | FastAPI `get_db` and `get_current_user` dependencies |
| `tameerai/backend/app/models/base.py` | SQLAlchemy `Base` with `created_at` and `updated_at` |
| `tameerai/backend/app/models/user.py` | `User` ORM model (email, password_hash, full_name, role, etc.) |
| `tameerai/backend/app/schemas/auth.py` | `LoginRequest`, `RegisterRequest`, `TokenResponse` |
| `tameerai/backend/app/schemas/user.py` | `UserProfile`, `UserRead`, `UserUpdate` |
| `tameerai/backend/app/services/auth_service.py` | User registration and authentication business logic |
| `tameerai/backend/app/api/v1/endpoints/auth.py` | `/auth/register`, `/auth/login`, `/auth/me` endpoints |
| `tameerai/backend/app/api/v1/api.py` | Aggregated v1 API router |
| `tameerai/backend/app/main.py` | Refactored FastAPI app including CORS, global handlers, and v1 router |
| `tameerai/backend/tests/conftest.py` | Pytest async client fixtures |
| `tameerai/backend/tests/test_auth.py` | Unit & integration tests for authentication |

---

## 6. Preservation Strategy for Existing Backend Prototype

- **`tameerai/backend/app/main.py`:** Currently has a simple `/projects` mock CRUD. During Phase 01, we will preserve the `/` health-check route, and safely mount the legacy `/projects` temporary mock endpoints alongside `/api/v1` so that nothing breaks if another tool relies on it, until Phase 02 replaces `/projects` with true database persistence.
- **`app/database/fake_db.py`**, **`app/routers/projects.py`**, **`app/schemas/project.py`**: These files are currently empty (0-1 bytes) and will be cleanly populated in Phase 01 and Phase 02.

---

## 7. Step-by-Step Phase 01 Execution Steps

When approved by the user, Phase 01 will execute in the following exact sequence:
1. **Dependency Installation:** Activate `tameerai/backend/venv` and install `requirements.txt`.
2. **Configuration & Core Setup:** Create `app/core/config.py`, `app/core/database.py`, `app/core/security.py`, and `app/core/deps.py`.
3. **ORM Models & Alembic Init:** Create `app/models/base.py` and `app/models/user.py`. Run `alembic init -t async alembic` (or configure async `env.py`).
4. **Initial Migration:** Generate and apply the first migration creating the `users` table.
5. **Pydantic Schemas:** Create `app/schemas/auth.py` and `app/schemas/user.py`.
6. **Auth Service & API Routers:** Implement `app/services/auth_service.py`, `app/api/v1/endpoints/auth.py`, and mount in `app/main.py` with CORS configured for `http://localhost:3000`.
7. **Verification & Tests:** Run automated pytest test suite (`pytest tests/test_auth.py`) verifying token issuance, password security, and user retrieval.

---

## 8. Verification & Acceptance Criteria

Phase 01 will be deemed complete when:
- `pytest tests/test_auth.py` passes 100%.
- Server starts cleanly via `uvicorn app.main:app --reload --port 8000`.
- Calling `POST /api/v1/auth/register` creates a user in PostgreSQL and returns a valid JWT.
- Calling `GET /api/v1/auth/me` with `Authorization: Bearer <token>` returns the user profile matching the frontend `UserProfile` interface.
- Calling from the Next.js origin (`http://localhost:3000`) succeeds without CORS errors.

