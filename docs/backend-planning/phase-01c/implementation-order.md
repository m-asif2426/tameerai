# TameerAI — Implementation Order & Phased Execution Strategy (Phase 01C)

**Project:** TameerAI — Pakistan Construction Compliance and Cost Intelligence  
**Milestone:** Phase 01C Roadmap Breakdown  
**Revision:** Post-Audit Corrected Version (19 Tables Across 6 Sub-Phases)

---

## 1. Sub-Phase Architecture

To maintain high code quality, strict testing, and prevent merge conflicts or regression, Phase 01C is segmented into 6 atomic sub-phases covering all **19 relational tables**:

```
Phase 01C.1: Database Schema & Frontend Contract Analysis (CURRENT - DESIGN ONLY)
      │
      ▼
Phase 01C.2: User & Authentication Models + Revision 01 Migration (3 Tables)
      │
      ▼
Phase 01C.3: Projects & Document Management Models + Revision 02 Migration (4 Tables)
      │
      ▼
Phase 01C.4: Engineering Intelligence Models (Compliance, Contract, Cost, Reports) + Revision 03 (8 Tables)
      │
      ▼
Phase 01C.5: Chat & Vector Knowledgebase Models + Revision 04 (4 Tables)
      │
      ▼
Phase 01C.6: Seed Data Scripts & Full Integration Test Verification
```

---

## 2. Sub-Phase Breakdown & Deliverables

### Phase 01C.1: Analysis & Architectural Design (Completed)
- **Objective:** Map all frontend TypeScript interfaces to PostgreSQL columns, verify Supabase schema state, reconcile all 19 relational tables, establish dual identifier pattern (`UUID` + `code`), enforce 1:1 `user_settings` cardinality, formulate project role hierarchy, and establish RAG tenant isolation.
- **Status:** Complete. Zero application code or database tables created.

### Phase 01C.2: Identity, User Models & Settings (Next Authorized Step — 3 Tables)
- **Objective:** Create SQLAlchemy models for users, settings, and sessions; generate and apply Alembic Revision 01.
- **Tables (3):** `users`, `user_settings` (1:1 enforced), `user_sessions`.
- **Files to Create:**
  - `app/models/user.py`: `User`, `UserSettings`, `UserSession`.
  - `app/schemas/user.py`: Pydantic request/response schemas matching `UserProfile`.
  - `alembic/versions/001_create_user_tables.py`
  - `tests/test_user_models.py`
- **Dependencies:** `passlib[bcrypt]`, `python-jose`.

### Phase 01C.3: Projects & Document Storage (4 Tables)
- **Objective:** Create SQLAlchemy models for projects, workspace members, activities, and documents; generate and apply Alembic Revision 02.
- **Tables (4):** `projects`, `project_members`, `project_activities`, `documents`.
- **Files to Create:**
  - `app/models/project.py`: `Project`, `ProjectMember`, `ProjectActivity`.
  - `app/models/document.py`: `Document`.
  - `app/schemas/project.py`: `ProjectRead`, `ProjectCreate`.
  - `alembic/versions/002_create_project_and_document_tables.py`
  - `tests/test_project_models.py`

### Phase 01C.4: Engineering Intelligence (8 Tables)
- **Objective:** Create models for compliance audits, CAD coordinate markers, contract risk cards, material rates, BOQ lines, and reports; generate and apply Alembic Revision 03.
- **Tables (8):**
  - `compliance_audits`, `compliance_findings`
  - `contract_analyses`, `contract_risk_cards`
  - `material_rates`, `boq_analyses`, `boq_items`
  - `reports`
- **Files to Create:**
  - `app/models/compliance.py`: `ComplianceAudit`, `ComplianceFinding`.
  - `app/models/contract.py`: `ContractAnalysis`, `ContractRiskCard`.
  - `app/models/cost.py`: `MaterialRate`, `BOQAnalysis`, `BOQItem`.
  - `app/models/report.py`: `Report`.
  - `alembic/versions/003_create_engineering_tables.py`
  - `tests/test_engineering_models.py`

### Phase 01C.5: Conversational AI & Vector Knowledgebase (4 Tables)
- **Objective:** Create models for chat sessions, messages with citation JSONB, and document chunks with parameterized `vector` type; generate and apply Alembic Revision 04.
- **Tables (4):** `chat_sessions`, `chat_messages`, `knowledge_sources`, `document_chunks`.
- **Files to Create:**
  - `app/models/chat.py`: `ChatSession`, `ChatMessage`.
  - `app/models/knowledge.py`: `KnowledgeSource`, `DocumentChunk`.
  - `alembic/versions/004_create_chat_and_vector_tables.py`
  - `tests/test_chat_models.py`

### Phase 01C.6: Seed Scripts & Full Database Health Verification
- **Objective:** Seed live material commodity rates (Lahore, Karachi, Islamabad) and sample project benchmarks matching frontend mock data.
- **Files to Create:**
  - `scripts/seed_material_rates.py`
  - `scripts/seed_demo_project.py`
  - `tests/test_seed_integrity.py`
