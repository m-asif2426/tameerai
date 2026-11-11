# TameerAI — Implementation Roadmap & Phased Execution Plan (Phase 00)

**Project:** TameerAI — AI Construction Compliance and Cost Intelligence  
**Objective:** Staged, incremental backend engineering plan designed for seamless integration with the existing Next.js frontend without breaking existing working UI.

---

## Roadmap Overview

```
Phase 01: Core Foundation, DB Setup & Authentication
    │
    ▼
Phase 02: Projects & Document Management
    │
    ▼
Phase 03: Knowledge Base Vectorization (PBC 2021 & FIDIC)
    │
    ▼
Phase 04: AI Construction Chat & Verifiable RAG Citations
    │
    ▼
Phase 05: Building-Code Compliance Engine & CAD Pinning
    │
    ▼
Phase 06: FIDIC & PEC Contract Risk Analysis Engine
    │
    ▼
Phase 07: BOQ & Live Material Cost Intelligence (Lahore, Karachi, Islamabad)
    │
    ▼
Phase 08: Multi-Agent Audit Pipeline & Bilingual Report Generation
    │
    ▼
Phase 09: System Integration, Security Hardening & Performance
```

---

## Phase 01: Core Backend Foundation, Config, Database & Authentication

### 1. Objective
Establish the foundational asynchronous FastAPI application, configure Pydantic Settings, connect PostgreSQL with Alembic migrations, and implement secure user registration, login, and JWT token issuance.

### 2. Existing Files to Reuse
- `tameerai/backend/app/main.py`: Adapt basic FastAPI app declaration and incorporate CORS middleware.
- `tameerai/frontend/src/services/apiClient.ts`: Preserved as the reference client expecting `http://localhost:8000/api/v1` and Bearer JWT.

### 3. New Files Required
- `tameerai/backend/app/core/config.py` (Pydantic settings)
- `tameerai/backend/app/core/database.py` (SQLAlchemy async engine & session)
- `tameerai/backend/app/core/security.py` (Password hashing & JWT)
- `tameerai/backend/app/core/deps.py` (FastAPI dependency injection)
- `tameerai/backend/app/models/base.py`, `app/models/user.py`
- `tameerai/backend/app/schemas/auth.py`, `app/schemas/user.py`
- `tameerai/backend/app/api/v1/api.py`, `app/api/v1/endpoints/auth.py`, `app/api/v1/endpoints/users.py`
- `tameerai/backend/app/services/auth_service.py`
- `tameerai/backend/alembic.ini`, `alembic/env.py`
- `tameerai/backend/.env.example`, `requirements.txt`

### 4. Dependencies
- `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `passlib[bcrypt]`, `python-jose[cryptography]`, `httpx`, `pytest`, `pytest-asyncio`

### 5. API Contracts
- `POST /api/v1/auth/register` -> Returns `{ access_token, token_type, user }`
- `POST /api/v1/auth/login` -> Returns `{ access_token, token_type, user }`
- `GET /api/v1/auth/me` -> Returns `UserProfile`
- `GET /api/v1/health` -> Returns `{"status": "ok", "database": "connected"}`

### 6. Tests
- Unit tests: password hashing, token expiration, JWT decode.
- Integration tests: register new user, login with valid/invalid credentials, access protected `/auth/me` with and without Bearer token.

### 7. Acceptance Criteria
- Running `alembic upgrade head` generates the `users` table in PostgreSQL.
- Both registration and login successfully return a valid JWT token.
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/auth/me` returns 200 OK with user profile.

---

## Phase 02: Projects & Document Management

### 1. Objective
Replace the in-memory `project_db` in `main.py` with persistent PostgreSQL storage matching all 17+ fields expected by the frontend `Project` interface, and implement file upload handling for project documents.

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/project.ts`: Source of truth for Project and Document data models.
- `tameerai/frontend/src/data/projects.ts`: Seed data source (`INITIAL_PROJECTS`).
- `tameerai/backend/app/main.py`: Deprecate `project_db` and route through new API router.

### 3. New Files Required
- `tameerai/backend/app/models/project.py`, `app/models/document.py`
- `tameerai/backend/app/schemas/project.py`, `app/schemas/document.py`
- `tameerai/backend/app/api/v1/endpoints/projects.py`, `app/api/v1/endpoints/documents.py`
- `tameerai/backend/app/services/project_service.py`, `app/services/document_service.py`
- `tameerai/backend/app/storage/file_manager.py` (upload directory handler)

### 4. Dependencies
- `python-multipart` (for multipart form file uploads), `aiofiles`

### 5. API Contracts
- `GET /api/v1/projects` (Supports query filters: `city`, `status`, `risk`, `search`)
- `POST /api/v1/projects` (Create project with Urdu translations)
- `GET /api/v1/projects/{id}`
- `DELETE /api/v1/projects/{id}`
- `GET /api/v1/projects/{id}/documents`
- `POST /api/v1/projects/{id}/documents` (Multipart upload)

### 6. Tests
- Seeding test: Load `INITIAL_PROJECTS` into database.
- Project CRUD test: verify bilingual fields (`nameUrdu`, `cityUrdu`, `statusUrdu`).
- File upload test: upload sample PDF and DWG, verify disk persistence and database record.

### 7. Acceptance Criteria
- Frontend `projectService.getProjects()` can point to `/api/v1/projects` and render without type or layout errors.
- New projects created via the frontend modal persist across browser refreshes and server restarts.

---

## Phase 03: Knowledge Base Vectorization (PBC 2021 & FIDIC)

### 1. Objective
Establish a vector retrieval database (`pgvector`) containing embedded Pakistan Building Code (PBC 2021) chapters, local zoning bylaws (LDA, SBCA, CDA), and standard construction contracts (FIDIC Red Book, PEC Standard Bidding Documents).

### 2. Existing Files to Reuse
- `tameerai/frontend/src/lib/dummy-data.ts`: Extract hardcoded references to PBC 2021 sections (e.g. Chapter 4, Table 4.1, Section 3.4).

### 3. New Files Required
- `tameerai/backend/app/models/vector.py` (Document chunks table with vector column)
- `tameerai/backend/app/ai/rag/embeddings.py` (Embedding generator wrapper)
- `tameerai/backend/app/ai/rag/chunker.py` (Structure-aware document chunker)
- `tameerai/backend/app/ai/rag/retriever.py` (Hybrid vector + keyword search)
- `tameerai/backend/scripts/ingest_pbc2021.py` (Seed script for PBC 2021 and FIDIC)

### 4. Dependencies
- `pgvector`, `langchain`, `langchain-community`, `google-generativeai`, `pypdf`, `pdfplumber`

### 5. API Contracts
- `GET /api/v1/knowledge/search?q={query}&library=pbc_2021` (Debug/Internal verification endpoint)

### 6. Tests
- Vector similarity search test: query "minimum stair width commercial" and assert top result is PBC 2021 Section 4.2.1.
- Metadata integrity test: verify chunk contains document ID, chapter, and page number.

### 7. Acceptance Criteria
- PostgreSQL `document_chunks` table populated with verified PBC 2021 text chunks.
- Vector query execution time < 100ms using IVFFlat cosine similarity index.

---

## Phase 04: AI Construction Chat & Verifiable RAG Citations

### 1. Objective
Implement the bilingual conversational AI assistant with verifiable document citations and structured "Warning Cards" matching the Next.js `ChatMessage` and `ChatWarningCard` schemas.

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/chat.ts`: Schema definition for `ChatMessage`, `ChatWarningCard`, `ChatCitation`.
- `tameerai/frontend/src/services/chatService.ts`: Replace mock returns with `apiClient.post(...)`.

### 3. New Files Required
- `tameerai/backend/app/models/chat.py` (Sessions and messages tables)
- `tameerai/backend/app/schemas/chat.py`
- `tameerai/backend/app/api/v1/endpoints/chat.py`
- `tameerai/backend/app/services/chat_service.py`
- `tameerai/backend/app/ai/prompts/chat_prompts.py` (Bilingual construction system instructions)

### 4. Dependencies
- `langchain-core`, `google-generativeai` (Gemini API)

### 5. API Contracts
- `GET /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/chat/sessions/{session_id}/messages` (Returns assistant response with citations and warning cards)

### 6. Tests
- Chat completion test: send prompt "Staircase width is 3.5 ft for commercial plaza" and verify response contains warning card with deficit and PBC citation.
- Bilingual output test: verify `contentUrdu` field is populated with accurate Urdu translation.

### 7. Acceptance Criteria
- User query in `src/app/dashboard/ai-assistant` displays real AI response, warning card, and clickable citations matching the existing UI component structure.

---

## Phase 05: Building-Code Compliance Engine & CAD Pinning

### 1. Objective
Implement automated compliance checking for architectural drawings against PBC 2021 and local development authority regulations (LDA, SBCA, CDA), returning pin coordinates `{x, y}` for the 2D CAD canvas.

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/compliance.ts`: `ComplianceRuleItem`, `ComplianceAuditSummary`.
- `tameerai/frontend/src/data/compliance.ts`: Reference benchmark violations.

### 3. New Files Required
- `tameerai/backend/app/models/compliance.py`
- `tameerai/backend/app/schemas/compliance.py`
- `tameerai/backend/app/api/v1/endpoints/compliance.py`
- `tameerai/backend/app/services/compliance_service.py`
- `tameerai/backend/app/ai/agents/compliance_agent.py`

### 4. Dependencies
- `ezdxf` (CAD DXF parsing) or `PyMuPDF` (PDF plan extraction)

### 5. API Contracts
- `GET /api/v1/compliance/summary?project_id={id}`
- `GET /api/v1/compliance/rules?project_id={id}&category={category}`
- `POST /api/v1/compliance/verify`

### 6. Tests
- Compliance rule evaluator unit tests: assert that 3.5ft width triggers "violation", 4.0ft triggers "passed".
- Coordinate serialization tests: ensure `pinCoordinates: { x: number, y: number }` are in 0-100% bounds.

### 7. Acceptance Criteria
- Compliance screen renders rule items and pins loaded dynamically from the backend for any selected project.

---

## Phase 06: FIDIC & PEC Contract Risk Analysis Engine

### 1. Objective
Implement legal NLP analysis for subcontractor and main contractor agreements, scanning for unlimited liquidated damages, delayed payment terms, and harsh termination clauses based on FIDIC Red Book and PEC guidelines.

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/contract.ts`: `ContractRiskCard`, `ContractAnalysisSummary`.
- `tameerai/frontend/src/data/contracts.ts`: Reference risk cards.

### 3. New Files Required
- `tameerai/backend/app/models/contract.py`
- `tameerai/backend/app/schemas/contract.py`
- `tameerai/backend/app/api/v1/endpoints/contracts.py`
- `tameerai/backend/app/services/contract_service.py`
- `tameerai/backend/app/ai/agents/contract_agent.py`

### 4. Dependencies
- `pypdf`, `langchain`

### 5. API Contracts
- `GET /api/v1/contracts/summary?project_id={id}`
- `GET /api/v1/contracts/risks?project_id={id}`
- `POST /api/v1/contracts/analyze`

### 6. Tests
- Contract clause extraction test: evaluate sample agreement with uncapped 0.5%/day delay damage, assert risk level is "high" and recommendation suggests 10% cap.

### 7. Acceptance Criteria
- Contract analyzer screen renders parsed risk cards and raw clause snippets from backend.

---

## Phase 07: BOQ & Live Material Cost Intelligence

### 1. Objective
Provide real-time construction commodity pricing (Grade 60 Steel, OPC Cement, Red Bricks, Sand, Aggregate) across Lahore, Karachi, and Islamabad, calculate BOQ variance, and project milestone overruns.

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/cost.ts`: `PriceTrendPoint`, `BudgetComparisonPhase`, `MaterialCostCard`.
- `tameerai/frontend/src/data/materialRates.ts`: Initial price points for cities.

### 3. New Files Required
- `tameerai/backend/app/models/cost.py`
- `tameerai/backend/app/schemas/cost.py`
- `tameerai/backend/app/api/v1/endpoints/costs.py`
- `tameerai/backend/app/services/cost_service.py`
- `tameerai/backend/scripts/seed_material_rates.py`

### 4. Dependencies
- `openpyxl` (BOQ Excel processing)

### 5. API Contracts
- `GET /api/v1/costs/rates?city={city}` (Public)
- `GET /api/v1/costs/trends?city={city}`
- `GET /api/v1/costs/budget-comparison?project_id={id}`
- `GET /api/v1/costs/overview?project_id={id}`

### 6. Tests
- Financial math tests: calculate variance percentage and budget overrun correctly.
- Rate filtering test: verify changing city from Lahore to Karachi returns Karachi specific rates.

### 7. Acceptance Criteria
- Landing page and Cost Intelligence screen render live price charts and rates fetched from backend.

---

## Phase 08: Multi-Agent Audit Pipeline & Bilingual Report Generation

### 1. Objective
Connect the 3-step New Audit wizard to a LangGraph multi-agent background job and generate downloadable executive PDF dossiers (Arup / Turner & Townsend format).

### 2. Existing Files to Reuse
- `tameerai/frontend/src/types/audit.ts`, `src/types/report.ts`
- `tameerai/frontend/src/data/reports.ts`

### 3. New Files Required
- `tameerai/backend/app/models/audit.py`, `app/models/report.py`
- `tameerai/backend/app/schemas/audit.py`, `app/schemas/report.py`
- `tameerai/backend/app/api/v1/endpoints/audits.py`, `app/api/v1/endpoints/reports.py`
- `tameerai/backend/app/services/audit_service.py`, `app/services/report_service.py`
- `tameerai/backend/app/ai/agents/graph.py` (LangGraph multi-agent orchestrator)
- `tameerai/backend/app/services/pdf_generator.py`

### 4. Dependencies
- `langgraph`, `reportlab` (or `weasyprint`)

### 5. API Contracts
- `POST /api/v1/audits` (Initiate background job)
- `GET /api/v1/audits/{job_id}/status`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{id}/download` (PDF binary)

### 6. Tests
- End-to-end background audit simulation test.
- PDF generation test: verify generated PDF contains watermark, project metadata, and bilingual findings.

### 7. Acceptance Criteria
- Clicking "Start Audit" in frontend triggers a real background job, updates progress dynamically, and allows downloading the resulting PDF report.

---

## Phase 09: System Integration, Security Hardening & Performance

### 1. Objective
Final end-to-end audit, CORS and security review, database indexing, Next.js route protection middleware, and load testing.

### 2. Tasks
- Audit all CORS origins, JWT expiration policies, and password hashing iterations.
- Add Next.js `middleware.ts` to redirect unauthenticated visitors from `/dashboard/*` to `/login`.
- Performance profiling for vector search and LLM response caching.
