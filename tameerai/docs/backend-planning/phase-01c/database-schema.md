# TameerAI — Complete PostgreSQL Database Schema Specification (Phase 01C.1 - Corrected)

**Project:** TameerAI — AI Construction Compliance and Cost Intelligence Platform  
**Target Database:** Supabase PostgreSQL 17.11 with `pgvector` 0.8.2  
**ORM Framework:** SQLAlchemy 2.0 (Asyncio) with Alembic  
**Status:** Architecture & Schema Design (Post-Review Corrected Specification)  
**Total Tables:** **19 Tables** (Reconciled from preliminary draft)  

---

## 1. Architectural & Schema Design Principles

1. **Table Count Reconciliation:** The schema consists of exactly **19 tables** organized into 5 logical clusters:
   - **Identity & Administration (3):** `users`, `user_settings`, `user_sessions`.
   - **Project Workspace & Collaboration (4):** `projects`, `project_members`, `project_activities`, `documents`.
   - **Conversational AI (2):** `chat_sessions`, `chat_messages`.
   - **Engineering Intelligence (8):** `compliance_audits`, `compliance_findings`, `contract_analyses`, `contract_risk_cards`, `material_rates`, `boq_analyses`, `boq_items`, `reports`.
   - **RAG Knowledgebase & Vectors (2):** `knowledge_sources`, `document_chunks`.
2. **Identifier Architecture (Dual Strategy):**
   - **Internal Relational Integrity:** All entity relationships and foreign keys are anchored to immutable, high-entropy `UUID` primary keys (`DEFAULT gen_random_uuid()`).
   - **Public-Facing Routing Codes:** Entities exposed to the frontend with human-readable identifiers (such as `projects`, `documents`, `compliance_findings`, `contract_risk_cards`, `reports`) feature an indexed `code VARCHAR(50)` (e.g. `PRJ-001`, `DOC-01`, `RULE-001`).
   - **Multi-Tenant Uniqueness:** Human-readable codes are constrained with composite uniqueness `UNIQUE (user_id, code)` or `UNIQUE (project_id, code)` to prevent ID collisions when different users create projects with matching numbers.
   - **API Serialization:** FastAPI routes accept either the UUID or the human-readable code seamlessly, serializing `code` to the frontend's expected `id` field.
3. **1:1 User Settings Cardinality:** `user_settings.user_id` has a strict `UNIQUE` constraint ensuring exactly one configuration record per user.
4. **Embedding Dimension Flexibility:** No premature commitment is made to `vector(768)` or specific embedding vendors. Vector columns are typed generically as `vector` and will be dimensioned only after the embedding model is benchmarked in the AI phase.
5. **RAG Scope Isolation:** `document_chunks` includes an explicit database constraint ensuring that public regulatory codices (PBC 2021) and confidential user blueprints can never be cross-pollinated or leaked across user boundaries.

---

## 2. Table-by-Table Technical Specifications (19 Tables)

---

### 2.1 Core Identity & Administration (Tables 1–3)

#### Table 1: `users`
Represents registered civil engineers, contractors, architects, and corporate firms.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'engineer',
    company VARCHAR(150),
    pec_number VARCHAR(100),
    phone VARCHAR(30),
    city VARCHAR(100) DEFAULT 'Lahore',
    bio TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_role CHECK (role IN ('engineer', 'contractor', 'architect', 'company', 'admin'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### Table 2: `user_settings`
Stores user notification preferences, interface language, theme, and AI strictness controls. Enforces strict 1:1 cardinality with `users`.

```sql
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    theme VARCHAR(10) NOT NULL DEFAULT 'light',
    pbc_violations_alert BOOLEAN NOT NULL DEFAULT TRUE,
    fidic_risks_alert BOOLEAN NOT NULL DEFAULT TRUE,
    price_spikes_alert BOOLEAN NOT NULL DEFAULT TRUE,
    weekly_digest BOOLEAN NOT NULL DEFAULT FALSE,
    whatsapp_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    ai_strictness VARCHAR(20) NOT NULL DEFAULT 'strict',
    fidic_threshold VARCHAR(10) NOT NULL DEFAULT '8',
    auto_citations BOOLEAN NOT NULL DEFAULT TRUE,
    market_region VARCHAR(50) NOT NULL DEFAULT 'lahore',
    ai_tone VARCHAR(20) NOT NULL DEFAULT 'professional',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_settings_user_id UNIQUE (user_id),
    CONSTRAINT fk_user_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### Table 3: `user_sessions`
Tracks active device logins for the Account Security tab.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_label VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50),
    location VARCHAR(100),
    refresh_token_hash VARCHAR(255),
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    last_active TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
```

---

### 2.2 Project Workspace & Collaboration (Tables 4–7)

#### Table 4: `projects`
Core project entity matching `Project` in `src/types/project.ts`. Uses internal UUID with a tenant-scoped public code.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. PRJ-001, PRJ-DHA-01
    user_id UUID NOT NULL,     -- Owner of the project
    name VARCHAR(200) NOT NULL,
    name_urdu VARCHAR(200),
    location VARCHAR(255) NOT NULL,
    location_urdu VARCHAR(255),
    city VARCHAR(50) NOT NULL DEFAULT 'Lahore',
    city_urdu VARCHAR(50) DEFAULT 'لاہور',
    type VARCHAR(100) NOT NULL DEFAULT 'Commercial',
    type_urdu VARCHAR(100) DEFAULT 'کمرشل',
    budget_crore NUMERIC(10, 4) NOT NULL DEFAULT 0.0000,
    budget_raw NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    spent_crore NUMERIC(10, 4) NOT NULL DEFAULT 0.0000,
    status VARCHAR(50) NOT NULL DEFAULT 'Planning',
    status_urdu VARCHAR(100) DEFAULT 'منصوبہ بندی (Planning)',
    risk VARCHAR(20) NOT NULL DEFAULT 'Low',
    risk_urdu VARCHAR(50) DEFAULT 'کم (Low)',
    compliance_score INTEGER NOT NULL DEFAULT 100,
    floors INTEGER NOT NULL DEFAULT 1,
    area_sqft VARCHAR(50) NOT NULL DEFAULT 'N/A',
    engineer VARCHAR(150),
    governing_authority VARCHAR(150) DEFAULT 'PBC 2021 & LDA',
    handover_date VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_projects_user_code UNIQUE (user_id, code),
    CONSTRAINT fk_projects_owner FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_code ON projects(code);
CREATE INDEX idx_projects_city ON projects(city);
CREATE INDEX idx_projects_status ON projects(status);
```

#### Table 5: `project_members`
Facilitates collaborative multi-user access (Architects, Contractors, Site Supervisors).

```sql
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_member UNIQUE (project_id, user_id),
    CONSTRAINT ck_project_member_role CHECK (role IN ('owner', 'lead_engineer', 'architect', 'contractor', 'viewer')),
    CONSTRAINT fk_project_members_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_project_members_proj ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
```

#### Table 6: `project_activities`
Maintains an audit trail of actions taken in the project workspace.

```sql
CREATE TABLE project_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    action_urdu VARCHAR(255),
    detail TEXT,
    activity_type VARCHAR(50) NOT NULL DEFAULT 'upload',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_activities_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_activities_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_project_activities_project ON project_activities(project_id);
```

#### Table 7: `documents`
Tracks all uploaded blueprints, drawings, Excel schedules, and contract files.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. DOC-01
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    file_size_human VARCHAR(30) NOT NULL DEFAULT '0 KB',
    storage_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'Pending Analysis',
    analysis_status VARCHAR(50) NOT NULL DEFAULT 'unprocessed',
    uploaded_by VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_documents_project_code UNIQUE (project_id, code),
    CONSTRAINT fk_documents_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_documents_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_code ON documents(code);
```

---

### 2.3 Conversational AI Assistant (Tables 8–9)

#### Table 8: `chat_sessions`
Represents conversational threads in the AI Assistant interface.

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. session-1
    user_id UUID NOT NULL,
    project_id UUID,
    title VARCHAR(200) NOT NULL,
    title_urdu VARCHAR(200),
    type VARCHAR(50) NOT NULL DEFAULT 'general',
    preview VARCHAR(255),
    preview_urdu VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_chat_sessions_user_code UNIQUE (user_id, code),
    CONSTRAINT fk_chat_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_sessions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_project ON chat_sessions(project_id);
CREATE INDEX idx_chat_sessions_updated ON chat_sessions(updated_at DESC);
```

#### Table 9: `chat_messages`
Stores individual conversation turns with rich metadata (citations and warning cards).

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. msg-171234
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    content_urdu TEXT,
    warning_card JSONB,
    citations JSONB,
    attachments JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_messages_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at ASC);
```

---

### 2.4 Engineering Intelligence & Cost (Tables 10–17)

#### Table 10: `compliance_audits`
Audit run records for a project plan against governing building codes.

```sql
CREATE TABLE compliance_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    document_id UUID,
    user_id UUID NOT NULL,
    overall_score INTEGER NOT NULL DEFAULT 0,
    total_checks INTEGER NOT NULL DEFAULT 0,
    passed_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    governing_code VARCHAR(150) NOT NULL DEFAULT 'Pakistan Building Code (PBC 2021)',
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_compliance_audits_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_compliance_audits_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_compliance_audits_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_compliance_audits_project ON compliance_audits(project_id);
```

#### Table 11: `compliance_findings`
Individual rule inspection findings with CAD blueprint pinpoint coordinates.

```sql
CREATE TABLE compliance_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. RULE-001
    audit_id UUID NOT NULL,
    project_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    category_name_urdu VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    title_urdu VARCHAR(200),
    status VARCHAR(50) NOT NULL,
    required_value VARCHAR(100) NOT NULL,
    current_value VARCHAR(100) NOT NULL,
    variance VARCHAR(100),
    reference_code VARCHAR(100) NOT NULL,
    reference_clause VARCHAR(200) NOT NULL,
    location_grid VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    description_urdu TEXT,
    remedy TEXT NOT NULL,
    remedy_urdu TEXT,
    pin_x NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    pin_y NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_compliance_findings_audit_code UNIQUE (audit_id, code),
    CONSTRAINT fk_compliance_findings_audit FOREIGN KEY (audit_id) REFERENCES compliance_audits(id) ON DELETE CASCADE,
    CONSTRAINT fk_compliance_findings_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_compliance_findings_audit ON compliance_findings(audit_id);
CREATE INDEX idx_compliance_findings_category ON compliance_findings(category);
CREATE INDEX idx_compliance_findings_status ON compliance_findings(status);
```

#### Table 12: `contract_analyses`
Contract evaluation run header.

```sql
CREATE TABLE contract_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    document_id UUID,
    user_id UUID NOT NULL,
    contract_title VARCHAR(255) NOT NULL,
    standard_format VARCHAR(100) NOT NULL DEFAULT 'FIDIC Red Book 2017 & PEC',
    risk_score NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    risk_category VARCHAR(50) NOT NULL DEFAULT 'Low Risk',
    total_clauses_audited INTEGER NOT NULL DEFAULT 0,
    flagged_clauses_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contract_analyses_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_contract_analyses_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_contract_analyses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_contract_analyses_project ON contract_analyses(project_id);
```

#### Table 13: `contract_risk_cards`
Flagged legal clauses and liability exposure cards.

```sql
CREATE TABLE contract_risk_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. risk-delay
    analysis_id UUID NOT NULL,
    clause_title VARCHAR(255) NOT NULL,
    clause_title_urdu VARCHAR(255),
    fidic_reference VARCHAR(150) NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    risk_level VARCHAR(20) NOT NULL,
    risk_level_label VARCHAR(100) NOT NULL,
    risk_level_label_urdu VARCHAR(100),
    explanation TEXT NOT NULL,
    explanation_urdu TEXT,
    recommendation TEXT NOT NULL,
    recommendation_urdu TEXT,
    impact_metric VARCHAR(150),
    raw_clause_snippet TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_contract_risk_cards_analysis_code UNIQUE (analysis_id, code),
    CONSTRAINT fk_contract_risk_cards_analysis FOREIGN KEY (analysis_id) REFERENCES contract_analyses(id) ON DELETE CASCADE
);

CREATE INDEX idx_contract_risk_cards_analysis ON contract_risk_cards(analysis_id);
CREATE INDEX idx_contract_risk_cards_level ON contract_risk_cards(risk_level);
```

#### Table 14: `material_rates`
Time-series market prices for major construction commodities in Pakistani cities.

```sql
CREATE TABLE material_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city VARCHAR(50) NOT NULL,
    name VARCHAR(150) NOT NULL,
    name_urdu VARCHAR(150),
    spec VARCHAR(200),
    spec_urdu VARCHAR(200),
    unit VARCHAR(50) NOT NULL,
    unit_urdu VARCHAR(50),
    rate_pkr NUMERIC(12, 2) NOT NULL,
    change_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    trend VARCHAR(20) NOT NULL DEFAULT 'neutral',
    primary_brands VARCHAR(255),
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_material_city_name_date UNIQUE (city, name, recorded_date)
);

CREATE INDEX idx_material_rates_city ON material_rates(city);
CREATE INDEX idx_material_rates_date ON material_rates(recorded_date DESC);
```

#### Table 15: `boq_analyses`
Project-level financial baseline vs estimated execution cost summary.

```sql
CREATE TABLE boq_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    document_id UUID,
    user_id UUID NOT NULL,
    project_budget NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    estimated_cost NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    cost_variance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    variance_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    risk_indicator VARCHAR(20) NOT NULL DEFAULT 'Low',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_boq_analyses_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_boq_analyses_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_boq_analyses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_boq_analyses_project ON boq_analyses(project_id);
```

#### Table 16: `boq_items`
Itemized BOQ lines and milestone phases (Foundation, RCC Superstructure, Finishing).

```sql
CREATE TABLE boq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    phase VARCHAR(100) NOT NULL,
    phase_urdu VARCHAR(100),
    item_code VARCHAR(50),
    description TEXT NOT NULL,
    spec VARCHAR(200),
    unit VARCHAR(50) NOT NULL,
    unit_urdu VARCHAR(50),
    quantity NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    boq_base_rate NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    current_price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    budget_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    estimated_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    overrun_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    variance_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_boq_items_analysis FOREIGN KEY (analysis_id) REFERENCES boq_analyses(id) ON DELETE CASCADE
);

CREATE INDEX idx_boq_items_analysis ON boq_items(analysis_id);
CREATE INDEX idx_boq_items_phase ON boq_items(phase);
```

#### Table 17: `reports`
Generated consulting engineering dossiers ready for download.

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL, -- e.g. RPT-001
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    title_urdu VARCHAR(255),
    category VARCHAR(50) NOT NULL,
    category_label VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'certified',
    status_label VARCHAR(100) NOT NULL,
    status_label_urdu VARCHAR(100),
    file_size VARCHAR(50) NOT NULL DEFAULT '0 MB',
    page_count INTEGER NOT NULL DEFAULT 1,
    author VARCHAR(150) NOT NULL DEFAULT 'TameerAI Engineering Intelligence',
    file_path VARCHAR(500),
    executive_summary TEXT NOT NULL,
    key_metric VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_reports_project_code UNIQUE (project_id, code),
    CONSTRAINT fk_reports_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_reports_project ON reports(project_id);
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_code ON reports(code);
```

---

### 2.5 RAG Knowledgebase & Vector Storage (Tables 18–19)

#### Table 18: `knowledge_sources`
Tracks official regulatory books and standard engineering codices.

```sql
CREATE TABLE knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    short_code VARCHAR(50) NOT NULL, -- e.g. PBC_2021, LDA_2020, FIDIC_RED_2017
    jurisdiction VARCHAR(100) NOT NULL,
    authority VARCHAR(150) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '2021',
    effective_date DATE,
    total_pages INTEGER NOT NULL DEFAULT 0,
    storage_path VARCHAR(500),
    is_official_regulatory BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_knowledge_short_code UNIQUE (short_code)
);

CREATE INDEX idx_knowledge_short_code ON knowledge_sources(short_code);
CREATE INDEX idx_knowledge_jurisdiction ON knowledge_sources(jurisdiction);
```

#### Table 19: `document_chunks`
Stores chunked text and vector embeddings. Uses `vector` data type supported by pgvector. Dimension is parameterized (`DIM`) and will be created when the model is confirmed.

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_source_id UUID,
    project_document_id UUID,
    project_id UUID,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chapter VARCHAR(150),
    section VARCHAR(150),
    page_number INTEGER,
    content TEXT NOT NULL,
    content_urdu TEXT,
    token_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB,
    embedding vector, -- Dimension flexible (e.g. vector(DIM)); finalized in AI Phase
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_document_chunks_scope CHECK (
        (knowledge_source_id IS NOT NULL AND project_id IS NULL AND project_document_id IS NULL)
        OR
        (knowledge_source_id IS NULL AND project_id IS NOT NULL AND project_document_id IS NOT NULL)
    ),
    CONSTRAINT fk_chunks_knowledge FOREIGN KEY (knowledge_source_id) REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunks_document FOREIGN KEY (project_document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunks_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_knowledge ON document_chunks(knowledge_source_id);
CREATE INDEX idx_chunks_project ON document_chunks(project_id);
CREATE INDEX idx_chunks_section ON document_chunks(section);
```
- **Strict Scope Isolation Constraint (`ck_document_chunks_scope`):** Guarantees that every chunk is strictly either a public regulatory document (`knowledge_source_id IS NOT NULL`) OR a private project blueprint (`project_id IS NOT NULL`), making cross-user leakage impossible at the database constraint level.
