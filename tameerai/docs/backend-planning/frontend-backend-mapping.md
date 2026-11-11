# TameerAI — Frontend-to-Backend Integration Mapping (Phase 00)

**Project:** TameerAI — AI Construction Compliance and Cost Intelligence  
**Scope:** Complete Endpoint Contract Mapping for Every Frontend Route & Component  
**Status:** All Backend Contracts Below Are **Proposals** Designed for Seamless Frontend Integration  

---

## 1. Global API Conventions

### 1.1 Base URL & Prefix
- Frontend Base URL: Configured in `src/services/apiClient.ts` as `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"`.
- All proposed endpoints below are mounted under `/api/v1`.

### 1.2 Authentication Header
- Format: `Authorization: Bearer <access_token>`
- Token Storage: `localStorage.getItem("tameerai_token")`
- Error Format: `{"detail": "Error description string"}` (FastAPI standard format handled by `apiClient.ts`)

---

## 2. Page & Component Integration Specifications

---

### 2.1 Authentication: Login & Registration

#### 1. Actual File Path
- `tameerai/frontend/src/app/login/page.tsx`
- `tameerai/frontend/src/app/signup/page.tsx`
- `tameerai/frontend/src/components/auth/AuthSplitScreen.tsx`

#### 2. Existing Functionality
- Split-screen UI with construction imagery and marketing badges.
- Tab toggle between Login and Register modes.
- Role selector: Civil Engineer, Contractor, Architect, Construction Firm.
- Password visibility toggle, "Remember Me", Terms agreement checkbox.
- Form submit handler triggers a 1000ms `setTimeout` and forces `window.location.href = "/dashboard"`.

#### 3. Data Source
- **Mock / Simulated:** No network request is made; simulated redirect only.

#### 4. Required Backend Endpoints [PROPOSED]
- `POST /api/v1/auth/register` (User registration)
- `POST /api/v1/auth/login` (User login, OAuth2 compatible)
- `GET /api/v1/auth/me` (Current authenticated user profile)
- `POST /api/v1/auth/refresh` (Token refresh)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `POST /api/v1/auth/register`
**Request Body:**
```json
{
  "email": "user@tameerai.pk",
  "password": "SecurePassword123!",
  "full_name": "Aslam Bhai",
  "role": "engineer",
  "company": "Aslam Associates",
  "pec_number": "PEC/REG/CIVIL-44910"
}
```
**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "user": {
    "id": "usr-uuid-001",
    "email": "user@tameerai.pk",
    "full_name": "Aslam Bhai",
    "role": "engineer",
    "company": "Aslam Associates",
    "pec_number": "PEC/REG/CIVIL-44910",
    "city": "Lahore"
  }
}
```

##### `POST /api/v1/auth/login`
**Request Body (JSON or x-www-form-urlencoded):**
```json
{
  "username": "user@tameerai.pk",
  "password": "SecurePassword123!"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "user": {
    "id": "usr-uuid-001",
    "email": "user@tameerai.pk",
    "full_name": "Aslam Bhai",
    "role": "engineer"
  }
}
```

#### 6. Authentication Requirements
- Public endpoints for `login` and `register`.
- `GET /api/v1/auth/me` requires `Bearer` token.

#### 7. Backend Dependencies
- `passlib[bcrypt]` (password hashing)
- `python-jose[cryptography]` (JWT generation and validation)
- SQLAlchemy `User` table model

#### 8. Missing / Incomplete Functionality
- Frontend does not store the JWT in `localStorage.setItem("tameerai_token", ...)` upon successful response.
- No form validation error toast or inline API error state.
- Next.js root middleware is missing to protect `/dashboard/*` routes.

---

### 2.2 Dashboard Overview

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/page.tsx`

#### 2. Existing Functionality
- Welcome banner personalized with engineer name.
- Summary metric cards (Active Projects, Compliance Score, Cost Saved, AI Queries).
- Critical alert banner for compliance deficiencies.
- Recent projects table with status badges and risk pills.
- Modal for quick blueprint upload simulation.

#### 3. Data Source
- **Mock:** Inline hardcoded `recentProjects` array and simulated upload `setTimeout`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/dashboard/metrics` (Aggregate stats for authenticated user)
- `GET /api/v1/projects?limit=5&sort=recent` (Top recent projects)
- `GET /api/v1/compliance/critical-alerts` (Active high-risk alerts)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/dashboard/metrics`
**Response (200 OK):**
```json
{
  "active_projects": 3,
  "average_compliance_score": 88,
  "cost_saved_pkr": "PKR 8.2M",
  "ai_queries_count": 347,
  "critical_alerts_count": 1
}
```

#### 6. Authentication Requirements
- Requires valid `Bearer` token.

#### 7. Backend Dependencies
- Aggregate queries over `projects`, `compliance_audits`, and `ai_chats` tables.

#### 8. Missing / Incomplete Functionality
- Dashboard metrics are hardcoded; no React hook or fetch call exists.

---

### 2.3 Project Management & Creation

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/projects/page.tsx`
- `tameerai/frontend/src/services/projectService.ts`

#### 2. Existing Functionality
- Grid and table view toggling.
- Full search by name, location, engineer, ID.
- Multi-faceted filters by City (Lahore, Karachi, Islamabad), Status, and Risk level.
- Sorting by recent, budget ascending/descending, risk, and name.
- "Create New Project" modal with inputs for name, city, location, budget in Crores, and building type.

#### 3. Data Source
- **Mock:** Initialized with `INITIAL_PROJECTS` from `src/data/projects.ts`. Form submission appends to local React state.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/projects` (List projects with filtering, search, and pagination)
- `POST /api/v1/projects` (Create new project)
- `GET /api/v1/projects/{id}` (Retrieve single project)
- `DELETE /api/v1/projects/{id}` (Archive / delete project)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/projects?city=Lahore&risk=High&search=DHA`
**Query Parameters:**
- `city` (optional): `Lahore` | `Karachi` | `Islamabad`
- `risk` (optional): `Low` | `Medium` | `High`
- `status` (optional): `Active` | `Under Analysis` | `Planning` | `Completed`
- `search` (optional): string
- `sort_by` (optional): `recent` | `budgetDesc` | `budgetAsc` | `risk` | `name`

**Response (200 OK):**
```json
[
  {
    "id": "PRJ-001",
    "name": "DHA Commercial Plaza",
    "nameUrdu": "ڈی ایچ اے کمرشل پلازہ",
    "location": "Phase 6, Sector G, Lahore",
    "locationUrdu": "فیز 6، سیکٹر جی، لاہور",
    "city": "Lahore",
    "cityUrdu": "لاہور",
    "type": "Commercial G+12",
    "typeUrdu": "کمرشل پلازہ (G+12)",
    "budgetCrore": 12.0,
    "budgetRaw": 120000000,
    "spentCrore": 7.2,
    "status": "Under Analysis",
    "statusUrdu": "زیرِ تجزیہ (Under Analysis)",
    "risk": "Medium",
    "riskUrdu": "درمیانہ (Medium)",
    "complianceScore": 84,
    "lastUpdate": "2 hours ago",
    "lastUpdateUrdu": "2 گھنٹے پہلے",
    "floors": 13,
    "areaSqft": "45,000 sq ft",
    "engineer": "Engr. Tariq Mehmood",
    "governingAuthority": "DHA Lahore & PBC 2021",
    "handoverDate": "December 2024"
  }
]
```

##### `POST /api/v1/projects`
**Request Body:**
```json
{
  "name": "Gulberg Office Complex",
  "location": "Main Boulevard, Gulberg III",
  "city": "Lahore",
  "type": "Commercial G+8",
  "budgetCrore": 18.5,
  "floors": 9,
  "areaSqft": "38,000 sq ft"
}
```
**Response (201 Created):** Full `Project` object with generated `id` (e.g. `PRJ-005`), Urdu translations, and default status `Planning`.

#### 6. Authentication Requirements
- Requires `Bearer` token. Projects are scoped by user/firm tenant ID.

#### 7. Backend Dependencies
- SQLAlchemy `Project` model with Urdu helper translations.

#### 8. Missing / Incomplete Functionality
- Backend `app/main.py` currently only accepts `{name, location, budget: int}` and ignores all bilingual and engineering attributes.

---

### 2.4 Individual Project Workspace

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/projects/[id]/page.tsx`

#### 2. Existing Functionality
- 7 comprehensive workspace tabs: Overview, AI Chat, Documents, Compliance, Contracts, Cost, Reports.
- Project metadata header (status, governing authority, budget vs spent, compliance score).
- Activity feed and audit milestone tracker.
- Document repository table with download and upload buttons.

#### 3. Data Source
- **Mock:** Hardcoded constants `projectData`, `projectDocuments`, `activities`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/projects/{id}` (Workspace header details)
- `GET /api/v1/projects/{id}/documents` (Document repository listing)
- `POST /api/v1/projects/{id}/documents` (Upload file: CAD, PDF, Excel)
- `GET /api/v1/projects/{id}/activities` (Project audit activity trail)
- `GET /api/v1/projects/{id}/summary` (Unified tab metrics: compliance, contracts, costs)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `POST /api/v1/projects/{id}/documents`
**Request (multipart/form-data):**
- `file`: Binary file (.dwg, .pdf, .xlsx)
- `document_type`: `CAD Drawing` | `Architectural Blueprint` | `Legal Contract` | `BOQ Spreadsheet`

**Response (201 Created):**
```json
{
  "id": "DOC-06",
  "name": "Structural-Slab-Drawing-Rev5.dwg",
  "type": "CAD Drawing",
  "size": "14.2 MB",
  "uploadedBy": "Engr. Tariq",
  "uploadTime": "Just now",
  "status": "Pending Analysis"
}
```

#### 6. Authentication Requirements
- Requires `Bearer` token with project read/write permissions.

#### 7. Backend Dependencies
- Document storage service (Local disk or S3/MinIO), metadata tracking in PostgreSQL.

---

### 2.5 AI Assistant & Bilingual Construction Chat

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/ai-assistant/page.tsx`
- `tameerai/frontend/src/services/chatService.ts`

#### 2. Existing Functionality
- Left sidebar: Chat session history grouped by Today, Yesterday, and Previous.
- Center pane: Interactive chat stream with typing indicator, audio playback toggle, copy-to-clipboard, feedback thumbs, citation reference badges, and detailed "Warning Cards".
- Right sidebar: Grounded document reference viewer with PDF preview pane, document source metadata, and quick prompt suggestions.
- Keyword-based response simulator (`lower.includes("code")`, `lower.includes("contract")`).

#### 3. Data Source
- **Mock:** Client-side mock state using `setTimeout` and hardcoded citation cards.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/chat/sessions` (Retrieve list of chat sessions)
- `POST /api/v1/chat/sessions` (Create a new chat conversation)
- `GET /api/v1/chat/sessions/{session_id}/messages` (History of messages for a session)
- `POST /api/v1/chat/sessions/{session_id}/messages` (Submit user query; returns assistant response)
- `GET /api/v1/chat/sessions/{session_id}/stream` (SSE streaming endpoint for real-time token rendering)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `POST /api/v1/chat/sessions/{session_id}/messages`
**Request Body:**
```json
{
  "content": "What is the minimum staircase clear width required for commercial occupancy under PBC 2021?",
  "language": "en",
  "project_id": "PRJ-001",
  "attachments": []
}
```
**Response (200 OK):**
```json
{
  "id": "msg-889123",
  "role": "assistant",
  "content": "According to the **Pakistan Building Code (PBC 2021 - Chapter 4, Section 4.2.1)**, the minimum clear width for an egress stairway serving an occupant load exceeding 50 persons is **4.0 feet (48 inches / 1,220 mm)**.",
  "contentUrdu": "پاکستان بلڈنگ کوڈ (پی بی سی 2021) کے باب 4، سیکشن 4.2.1 کے تحت 50 سے زائد افراد کی کمرشل عمارت کے لیے سیڑھی کی کم از کم چوڑائی 4.0 فٹ (48 انچ) ہونا لازمی ہے۔",
  "timestamp": "10:32 AM",
  "warningCard": {
    "title": "Compliance Verification Note",
    "titleUrdu": "تعمیل کی تصدیق کا جائزہ",
    "referenceCode": "PBC 2021",
    "referenceSection": "Section 4.2.1",
    "referencePage": 38,
    "currentValue": "Queried Standard",
    "requiredValue": "4.0 feet clear width",
    "deficit": "Ensure no obstruction by handrails > 4.5 in",
    "recommendation": "Maintain minimum 48 inches between opposing handrails.",
    "recommendationUrdu": "سیڑھیوں کی ریلنگ کے درمیان کم از کم 48 انچ کلیئر فاصلہ برقرار رکھیں۔",
    "detailedNotes": [
      "Headroom clearance must be at least 6 ft 8 in (2,030 mm).",
      "Riser height maximum 7 inches (178 mm), tread run minimum 11 inches (279 mm)."
    ]
  },
  "citations": [
    {
      "code": "PBC 2021",
      "clause": "Section 4.2.1 (Minimum Stairway Width)",
      "docId": "doc-pbc-2021-ch4",
      "page": 38
    }
  ]
}
```

#### 6. Authentication Requirements
- Requires `Bearer` token.

#### 7. Backend Dependencies
- LangChain / LangGraph retrieval chain.
- PostgreSQL + `pgvector` index containing embedded PBC 2021 chapters.
- LLM API integration (e.g. Gemini 1.5 Pro / Flash via Google GenAI SDK).

#### 8. Missing / Incomplete Functionality
- Currently entirely simulated in component code. No connection to real RAG embeddings or vector search.

---

### 2.6 Audit Setup & Execution Wizard

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/audit/page.tsx`
- `tameerai/frontend/src/services/auditService.ts`

#### 2. Existing Functionality
- Step 1: Project Information (City, authority, covered area, budget, floors).
- Step 2: Upload Project Files (CAD architectural floor plans, BOQ Excel, FIDIC contract PDF, site inspection images).
- Step 3: Choose Analysis Type (Code Compliance, Contract Risk, Cost Intelligence, or Full Audit).
- Modal simulation with multi-stage progress bar showing tasks in English and Urdu.

#### 3. Data Source
- **Mock:** Component state with hardcoded preset values and simulated timer progression.

#### 4. Required Backend Endpoints [PROPOSED]
- `POST /api/v1/audits` (Initiate background audit job)
- `GET /api/v1/audits/{job_id}/status` (Check audit job status and progress percentage)
- `GET /api/v1/audits/{job_id}/results` (Retrieve finalized multi-agent audit dossier)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `POST /api/v1/audits`
**Request (multipart/form-data or JSON with uploaded document IDs):**
```json
{
  "project_name": "DHA Commercial Plaza",
  "building_type": "commercial",
  "city": "Lahore",
  "area_sqft": "45000",
  "budget_crores": 12.0,
  "floors": 6,
  "analysis_type": "full",
  "document_ids": ["doc-cad-01", "doc-boq-02", "doc-contract-03"]
}
```
**Response (202 Accepted):**
```json
{
  "job_id": "job-audit-99014",
  "status": "processing",
  "progress": 5,
  "current_task": "Parsing CAD drawings & calculating clear widths...",
  "current_task_urdu": "نقشے کا معائنہ اور چوڑائی کا حساب جاری..."
}
```

##### `GET /api/v1/audits/{job_id}/status`
**Response (200 OK):**
```json
{
  "job_id": "job-audit-99014",
  "status": "completed",
  "progress": 100,
  "current_task": "Audit Complete! Generating intelligence dashboard...",
  "current_task_urdu": "آڈٹ مکمل! انٹیلی جنس ڈیش بورڈ تیار ہے...",
  "result_summary": {
    "compliance_score": 84,
    "violations_count": 2,
    "warnings_count": 1,
    "contract_risk_score": 8,
    "cost_overrun_pct": 7.04
  }
}
```

#### 6. Authentication Requirements
- Requires `Bearer` token.

#### 7. Backend Dependencies
- Background task execution (FastAPI `BackgroundTasks` or Celery/Redis).
- Multi-agent orchestrator (LangGraph) coordinating compliance, contract, and cost agents.

---

### 2.7 Building Code Compliance Inspection

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/compliance/page.tsx`
- `tameerai/frontend/src/services/complianceService.ts`

#### 2. Existing Functionality
- Interactive blueprint canvas featuring zoom, pan, and interactive pins placed via `{x, y}` coordinates.
- Rule inspection items filtered by category (Means of Egress, Fire & Life Safety, Structural, Zoning).
- Severity status (Violation, Warning, Passed).
- Detailed side panel with exact PBC 2021 section references, current vs. required measurements, variance deficits, and bilingual corrective remedies.

#### 3. Data Source
- **Mock:** Loaded from `COMPLIANCE_ITEMS` and `COMPLIANCE_AUDIT_SUMMARY` in `src/data/compliance.ts`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/compliance/summary?project_id={id}` (Compliance score, total checks, breakdown)
- `GET /api/v1/compliance/rules?project_id={id}&category={category}` (List of inspected items with coordinates and clauses)
- `POST /api/v1/compliance/rules/{rule_id}/resolve` (Mark rule remediation as verified)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/compliance/rules?project_id=PRJ-001`
**Response (200 OK):**
```json
[
  {
    "id": "RULE-001",
    "category": "egress",
    "categoryName": "Means of Egress",
    "categoryNameUrdu": "اخراج کے راستے",
    "title": "Stair Width",
    "titleUrdu": "سیڑھی کی چوڑائی (Stair Width)",
    "status": "violation",
    "requiredValue": "4.0 feet (48 in / 1,220 mm)",
    "currentValue": "3.5 feet (42 in / 1,067 mm)",
    "variance": "-6.0 inches (-153 mm) Deficit",
    "referenceCode": "PBC 2021",
    "referenceClause": "Section 4.2.1 (Minimum Stairway Width)",
    "locationGrid": "Grid 4B - East Core Stairwell",
    "description": "Stairway serving an occupant load exceeding 50 persons lacks mandatory clear egress width.",
    "descriptionUrdu": "کمرشل عمارت میں 50 سے زائد افراد کے انخلا کے لیے سیڑھی کی چوڑائی مطلوبہ 4.0 فٹ سے 6 انچ کم ہے۔",
    "remedy": "Increase clear width by shifting partition wall along Grid 4B.",
    "remedyUrdu": "گرڈ 4B کے ساتھ والی دیوار کو پیچھے ہٹا کر سیڑھی کی چوڑائی 4 فٹ تک کریں۔",
    "pinCoordinates": { "x": 38, "y": 35 }
  }
]
```

#### 6. Authentication Requirements
- Requires `Bearer` token.

#### 7. Backend Dependencies
- Blueprint parsing rule-check engine with coordinate pinpointing.

---

### 2.8 Contract Risk Analysis

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/contracts/page.tsx`
- `tameerai/frontend/src/services/contractService.ts`

#### 2. Existing Functionality
- Executive contract risk overview (Risk score e.g. 8/10, standard format FIDIC Red Book, flagged clauses count).
- Filterable risk cards categorized into High, Medium, Low risk.
- Full details including raw clause snippet, FIDIC reference, financial exposure metrics, and bilingual recommendations.

#### 3. Data Source
- **Mock:** Loaded from `CONTRACT_RISKS` and `CONTRACT_ANALYSIS_SUMMARY` in `src/data/contracts.ts`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/contracts/summary?project_id={id}` (Contract audit summary metrics)
- `GET /api/v1/contracts/risks?project_id={id}&severity={severity}` (List of flagged risk cards)
- `POST /api/v1/contracts/analyze` (Upload contract PDF and extract risk clauses)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/contracts/risks?project_id=PRJ-001`
**Response (200 OK):**
```json
[
  {
    "id": "risk-delay",
    "clauseTitle": "Delay Clause (Liquidated Damages)",
    "clauseTitleUrdu": "تاخیر کا ہرجانہ شق (Delay Clause)",
    "fidicReference": "Sub-Clause 8.7 & Clause 14",
    "pageNumber": 12,
    "riskLevel": "high",
    "riskLevelLabel": "Critical Risk (8/10)",
    "riskLevelLabelUrdu": "انتہائی خطرہ (8/10)",
    "explanation": "Contract imposes liquidated damages of 0.5% per day without an aggregate liability cap.",
    "explanationUrdu": "معاہدے میں تاخیر پر بغیر کسی حد کے یومیہ 0.5 فیصد جرمانہ عائد کیا گیا ہے۔",
    "recommendation": "Insert an explicit aggregate delay damages cap of 10% under FIDIC guidelines.",
    "recommendationUrdu": "تاخیر کے جرمانے کی کل حد 10 فیصد مقرر کروائیں۔",
    "impactMetric": "Potential Uncapped Liability: PKR 24M+",
    "rawClauseSnippet": "8.7 Delay Damages: If the Subcontractor fails to complete the Works..."
  }
]
```

#### 6. Authentication Requirements
- Requires `Bearer` token.

#### 7. Backend Dependencies
- Legal NLP extraction agent specialized in FIDIC Red/Yellow books and Pakistan Engineering Council (PEC) standard bidding provisions.

---

### 2.9 Cost Intelligence & Material Rates

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/costs/page.tsx`
- `tameerai/frontend/src/services/costService.ts`
- `tameerai/frontend/src/components/landing/MaterialRatesSection.tsx`

#### 2. Existing Functionality
- Recharts historical and forecast price curves (May – Dec) for Steel (Grade 60), Cement (OPC), and Red Bricks.
- Milestone/Phase budget comparison bar charts (Foundation, RCC Superstructure, Finishing).
- City rate switcher (Lahore, Karachi, Islamabad).
- Material cost cards showing current prices, BOQ baseline variance, trends, and primary brands (Mughal, Amreli, Bestway, Lucky).

#### 3. Data Source
- **Mock:** Loaded from `PRICE_TRENDS_DATA`, `BUDGET_COMPARISON_DATA`, and `LIVE_RATES_BY_CITY` in `src/data/`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/costs/overview?project_id={id}` (Budget vs estimated cost, variance, risk)
- `GET /api/v1/costs/trends?city={city}&range=6m` (Price trends time series for Recharts)
- `GET /api/v1/costs/budget-comparison?project_id={id}` (Phase-wise budget vs estimated overrun)
- `GET /api/v1/costs/rates?city={city}` (Live local material market rates)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/costs/rates?city=Lahore`
**Response (200 OK):**
```json
[
  {
    "name": "Deformed Steel Gr.60",
    "nameUrdu": "ڈیفارمڈ سٹیل گریڈ 60",
    "unit": "per Ton",
    "unitUrdu": "فی ٹن",
    "rate": "PKR 248,500",
    "change": "+1.2%",
    "trend": "up",
    "brand": "Mughal / Ittefaq"
  },
  {
    "name": "OPC Cement (50kg)",
    "nameUrdu": "او پی سی سیمنٹ (50 کلو)",
    "unit": "per Bag",
    "unitUrdu": "فی بوری",
    "rate": "PKR 1,420",
    "change": "-0.7%",
    "trend": "down",
    "brand": "Bestway / Lucky"
  }
]
```

#### 6. Authentication Requirements
- `GET /api/v1/costs/rates` can be public (used on landing page).
- Project-specific budget endpoints require `Bearer` token.

#### 7. Backend Dependencies
- Daily/weekly rate scraping or database seeding for Pakistani construction materials.
- Mathematical BOQ calculations for overrun forecasting.

---

### 2.10 Reports Management & Generation

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/reports/page.tsx`
- `tameerai/frontend/src/services/reportService.ts`

#### 2. Existing Functionality
- Engineering dossiers filtered by category: Compliance, Contract, Cost, or All.
- Search and project filtering.
- Report preview modal showing executive summaries, key metrics, authors, and page counts.
- Simulated PDF download with toast notification.

#### 3. Data Source
- **Mock:** Loaded from `CONSULTING_REPORTS` in `src/data/reports.ts`.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/reports?category={category}&project_id={id}` (List reports)
- `GET /api/v1/reports/{id}` (Retrieve single report metadata)
- `POST /api/v1/reports/generate` (Generate a new PDF report)
- `GET /api/v1/reports/{id}/download` (Stream binary PDF file)

#### 5. Expected Request & Response Contract [PROPOSED]

##### `GET /api/v1/reports/{id}/download`
- **Response Headers:** `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="PRJ001_DHA_Plaza_Compliance_Certificate.pdf"`
- **Response Body:** Binary PDF stream.

#### 6. Authentication Requirements
- Requires `Bearer` token.

#### 7. Backend Dependencies
- PDF generation library (e.g. `reportlab`, `weasyprint`, or headless browser rendering).

---

### 2.11 Settings & User Profile

#### 1. Actual File Path
- `tameerai/frontend/src/app/dashboard/settings/page.tsx`

#### 2. Existing Functionality
- 6 settings sections: Profile, Language, Theme, Notifications, Security, AI Preferences.
- Profile fields: Full name, role, company, PEC registration number, email, phone, city, bio.
- Notification toggles: PBC violations, FIDIC risks, price spikes, weekly digest, WhatsApp alerts.
- AI settings: Strictness (strict vs. consultative), FIDIC risk threshold, auto-citations, market region, AI tone.
- Active device sessions listing.

#### 3. Data Source
- **Mock:** Local state initialized with `DEFAULT_USER_PROFILE`, `DEFAULT_AI_SETTINGS`, etc.

#### 4. Required Backend Endpoints [PROPOSED]
- `GET /api/v1/users/profile`
- `PUT /api/v1/users/profile`
- `GET /api/v1/users/preferences`
- `PUT /api/v1/users/preferences`
- `GET /api/v1/users/sessions`
- `DELETE /api/v1/users/sessions/{id}`

#### 5. Expected Request & Response Contract [PROPOSED]

##### `PUT /api/v1/users/profile`
**Request Body:**
```json
{
  "fullName": "Aslam Bhai (Thekedar)",
  "role": "Lead Contractor & Managing Partner",
  "company": "Aslam Construction Associates",
  "pecNumber": "PEC/REG/CIVIL-44910",
  "phone": "+92 300 8492011",
  "city": "Lahore",
  "bio": "Commercial plaza framing specialist."
}
```
**Response (200 OK):** Updated `UserProfile` object.

#### 6. Authentication Requirements
- Requires `Bearer` token.
