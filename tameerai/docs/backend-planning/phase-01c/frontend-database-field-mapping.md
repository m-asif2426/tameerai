# TameerAI — Frontend TypeScript to Database Field Mapping (Phase 01C.1)

**Project:** TameerAI — Pakistan Construction Compliance & Cost Intelligence  
**Purpose:** Precise contract alignment between Frontend TypeScript interfaces, Backend Pydantic models, and PostgreSQL columns.  
**Revision:** Post-Audit Corrected Version (Dual Identifier Architecture & 19 Tables Reconciled)

---

## 1. Dual Identifier Pattern & Serialization Architecture

### The Core Architectural Principle
- **Database Layer:** Uses native PostgreSQL `UUID` primary keys (`id UUID DEFAULT gen_random_uuid()`) for collision-free integrity, foreign key references, and optimal B-tree indexing.
- **Frontend Layer:** Expects human-friendly string identifiers (e.g., `PRJ-001`, `DOC-01`, `RULE-001`, `RPT-001`, `risk-delay`, `session-1`) across UI routes and state stores.
- **Mapping Strategy:**
  - PostgreSQL stores the human-readable identifier in a dedicated `code VARCHAR(50)` column with a scoped unique constraint (e.g., `UNIQUE(user_id, code)` or `UNIQUE(project_id, code)`).
  - Pydantic response models serialize `code` into the JSON `id` property:
    ```python
    class ProjectRead(BaseModel):
        id: str = Field(..., alias="code")  # Serializes DB 'code' as JSON 'id'
        uuid: UUID = Field(..., alias="id")  # Exposes internal DB UUID
        ...
        model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    ```
  - FastAPI path parameters accept polymorphic lookup:
    ```python
    # Endpoint: GET /api/v1/projects/{identifier}
    # Matches either UUID string or human-readable code
    ```
  This guarantees **100% backward compatibility** with the existing Next.js frontend without requiring frontend code refactoring, while eliminating multi-tenant collision risks.

---

## 2. Project Entity Mapping (`src/types/project.ts` -> `Project`)

| Frontend TypeScript Field (`Project`) | Frontend Type | Backend Pydantic Field | PostgreSQL Column | DB Type | Nature / Transformation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public code (e.g. `PRJ-001`). Internal DB PK is `id UUID`. |
| `name` | `string` | `name: str` | `name` | `VARCHAR(200)` | Direct storage |
| `nameUrdu` | `string` | `name_urdu: Optional[str]` | `name_urdu` | `VARCHAR(200)` | Direct storage (auto-fallback to `name` if omitted) |
| `location` | `string` | `location: str` | `location` | `VARCHAR(255)` | Direct storage |
| `locationUrdu` | `string?` | `location_urdu: Optional[str]`| `location_urdu` | `VARCHAR(255)` | Direct storage |
| `city` | `"Lahore" \| "Karachi" \| "Islamabad"` | `city: ProjectCityEnum` | `city` | `VARCHAR(50)` | Direct storage with enum validation |
| `cityUrdu` | `string` | `city_urdu: str` | `city_urdu` | `VARCHAR(50)` | Stored or computed from `city` map |
| `type` | `string` | `type: str` | `type` | `VARCHAR(100)` | Direct storage (e.g. `Commercial G+12`) |
| `typeUrdu` | `string` | `type_urdu: Optional[str]` | `type_urdu` | `VARCHAR(100)` | Direct storage |
| `budgetCrore` | `number` | `budget_crore: float` | `budget_crore` | `NUMERIC(10, 4)` | Direct storage in crore units |
| `budgetRaw` | `number` | `budget_raw: Optional[float]`| `budget_raw` | `NUMERIC(15, 2)` | **Computed/Derived**: `budget_crore * 10,000,000` |
| `spentCrore` | `number` | `spent_crore: float` | `spent_crore` | `NUMERIC(10, 4)` | Direct storage |
| `status` | `"Under Analysis" \| "Active" \| "Planning" \| "Completed"` | `status: ProjectStatusEnum` | `status` | `VARCHAR(50)` | Direct storage |
| `statusUrdu` | `string` | `status_urdu: str` | `status_urdu` | `VARCHAR(100)` | Direct storage or derived from `status` map |
| `risk` | `"Low" \| "Medium" \| "High"` | `risk: ProjectRiskEnum` | `risk` | `VARCHAR(20)` | Direct storage |
| `riskUrdu` | `string` | `risk_urdu: str` | `risk_urdu` | `VARCHAR(50)` | Direct storage or derived from `risk` map |
| `complianceScore` | `number` | `compliance_score: int` | `compliance_score`| `INTEGER` | Direct storage (calculated by compliance audit) |
| `lastUpdate` | `string` | `last_update: str` | *(Derived from `updated_at`)* | `TIMESTAMPTZ` | **Computed**: Backend converts `updated_at` to human-readable string (e.g. "2 hours ago") |
| `lastUpdateUrdu` | `string` | `last_update_urdu: str` | *(Derived from `updated_at`)* | `TIMESTAMPTZ` | **Computed**: Backend formats relative time in Urdu (e.g. "2 گھنٹے پہلے") |
| `floors` | `number` | `floors: int` | `floors` | `INTEGER` | Direct storage |
| `areaSqft` | `string` | `area_sqft: str` | `area_sqft` | `VARCHAR(50)` | Direct storage (e.g. "45,000 sq ft") |
| `engineer` | `string` | `engineer: Optional[str]` | `engineer` | `VARCHAR(150)` | Direct storage |
| `governingAuthority` | `string?` | `governing_authority: Optional[str]` | `governing_authority` | `VARCHAR(150)` | Direct storage |
| `handoverDate` | `string?` | `handover_date: Optional[str]` | `handover_date` | `VARCHAR(50)` | Direct storage |

---

## 3. Project Document Mapping (`src/types/project.ts` -> `ProjectDocument`)

| Frontend TypeScript Field (`ProjectDocument`) | Frontend Type | Backend Pydantic Field | PostgreSQL Column | DB Type | Nature / Transformation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public code (e.g. `DOC-01`). Internal DB PK is `id UUID`. |
| `name` | `string` | `name: str` | `name` | `VARCHAR(255)` | Filename (e.g. `Structural-Drawing.dwg`) |
| `type` | `string` | `file_type: str` | `file_type` | `VARCHAR(50)` | Category (`CAD Drawing`, `Legal Contract`, etc.) |
| `size` | `string` | `file_size_human: str` | `file_size_human` | `VARCHAR(30)` | Human-readable size (`42.5 MB`) |
| *(None in TS)* | — | `file_size_bytes: int` | `file_size_bytes` | `BIGINT` | Exact byte count stored in DB |
| `uploadedBy` | `string` | `uploaded_by: str` | `uploaded_by` | `VARCHAR(150)` | Name of uploader |
| `uploadTime` | `string` | `upload_time: str` | `created_at` | `TIMESTAMPTZ` | **Computed**: Relative time from `created_at` |
| `status` | `"Verified" \| "Review Required" \| "Pending Analysis"` | `status: str` | `status` | `VARCHAR(50)` | Direct storage |
| *(None in TS)* | — | `storage_path: str` | `storage_path` | `VARCHAR(500)` | Server storage file path |

---

## 4. AI Chat Session & Message Mapping (`src/types/chat.ts`)

### `ChatSession`
| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public session ID (`session-1`). DB PK is `id UUID`. |
| `title` | `string` | `title: str` | `title` | `VARCHAR(200)` | Conversation title |
| `titleUrdu` | `string` | `title_urdu: Optional[str]` | `title_urdu` | `VARCHAR(200)` | Urdu title |
| `category` | `"today" \| "yesterday" \| "previous"` | `category: str` | *(Computed)* | — | **Computed**: Calculated from `updated_at` date comparison with `CURRENT_DATE` |
| `timestamp` | `string` | `timestamp: str` | `updated_at` | `TIMESTAMPTZ` | **Computed**: Formatted time (e.g. "10:32 AM") |
| `preview` | `string` | `preview: Optional[str]` | `preview` | `VARCHAR(255)` | Snippet of last prompt |
| `previewUrdu` | `string` | `preview_urdu: Optional[str]`| `preview_urdu` | `VARCHAR(255)` | Urdu snippet |
| `type` | `"code" \| "contract" \| "cost" \| "general"` | `type: str` | `type` | `VARCHAR(50)` | Domain categorization |

### `ChatMessage`
| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public message ID (`msg-171234`). DB PK is `id UUID`. |
| `role` | `"user" \| "assistant"` | `role: str` | `role` | `VARCHAR(20)` | Speaker role |
| `content` | `string` | `content: str` | `content` | `TEXT` | Markdown response text |
| `contentUrdu` | `string?` | `content_urdu: Optional[str]` | `content_urdu` | `TEXT` | Parallel Urdu response |
| `timestamp` | `string` | `timestamp: str` | `created_at` | `TIMESTAMPTZ` | **Computed**: Formatted time string |
| `warningCard` | `ChatWarningCard?` | `warning_card: Optional[dict]` | `warning_card` | `JSONB` | Structured compliance/contract card |
| `citations` | `ChatCitation[]?` | `citations: Optional[List[dict]]` | `citations` | `JSONB` | Grounded reference badges |
| `attachments` | `string[]?` | `attachments: Optional[List[str]]`| `attachments` | `JSONB` | Attached document IDs |

---

## 5. Compliance Rule Item Mapping (`src/types/compliance.ts` -> `ComplianceRuleItem`)

| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public rule ID (e.g. `RULE-001`). DB PK is `id UUID`. |
| `category` | `"egress" \| "structural" \| "zoning" \| "fire"` | `category: str` | `category` | `VARCHAR(50)` | Enum value |
| `categoryName` | `string` | `category_name: str` | `category_name` | `VARCHAR(100)` | Label ("Means of Egress") |
| `categoryNameUrdu`| `string` | `category_name_urdu: str` | `category_name_urdu` | `VARCHAR(100)` | Label ("اخراج کے راستے") |
| `title` | `string` | `title: str` | `title` | `VARCHAR(200)` | Short title ("Stair Width") |
| `titleUrdu` | `string` | `title_urdu: str` | `title_urdu` | `VARCHAR(200)` | Short Urdu title |
| `status` | `"violation" \| "warning" \| "passed"` | `status: str` | `status` | `VARCHAR(50)` | Audit flag status |
| `requiredValue` | `string` | `required_value: str` | `required_value` | `VARCHAR(100)` | Code requirement measurement |
| `currentValue` | `string` | `current_value: str` | `current_value` | `VARCHAR(100)` | Measured measurement |
| `variance` | `string?` | `variance: Optional[str]` | `variance` | `VARCHAR(100)` | Deficit measurement |
| `referenceCode` | `string` | `reference_code: str` | `reference_code` | `VARCHAR(100)` | Code codex (e.g. `PBC 2021`) |
| `referenceClause` | `string` | `reference_clause: str` | `reference_clause` | `VARCHAR(200)` | Clause (e.g. `Section 4.2.1`) |
| `locationGrid` | `string` | `location_grid: str` | `location_grid` | `VARCHAR(100)` | Grid coordinate ("Grid 4B") |
| `description` | `string` | `description: str` | `description` | `TEXT` | Detailed explanation |
| `descriptionUrdu` | `string` | `description_urdu: str` | `description_urdu` | `TEXT` | Detailed Urdu explanation |
| `remedy` | `string` | `remedy: str` | `remedy` | `TEXT` | Engineering corrective action |
| `remedyUrdu` | `string` | `remedy_urdu: str` | `remedy_urdu` | `TEXT` | Corrective action in Urdu |
| `pinCoordinates` | `{ x: number, y: number }` | `pin_coordinates: dict` | `pin_x`, `pin_y` | `NUMERIC(5,2)` | Stored as separate columns; Pydantic packs into `{x, y}` object for frontend |

---

## 6. Contract Risk Card Mapping (`src/types/contract.ts` -> `ContractRiskCard`)

| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public risk ID (e.g. `risk-delay`). DB PK is `id UUID`. |
| `clauseTitle` | `string` | `clause_title: str` | `clause_title` | `VARCHAR(255)` | Clause header |
| `clauseTitleUrdu`| `string` | `clause_title_urdu: str` | `clause_title_urdu`| `VARCHAR(255)` | Urdu header |
| `fidicReference` | `string` | `fidic_reference: str` | `fidic_reference` | `VARCHAR(150)` | Reference (e.g. `Sub-Clause 8.7`) |
| `pageNumber` | `number` | `page_number: int` | `page_number` | `INTEGER` | Contract page |
| `riskLevel` | `"high" \| "medium" \| "low"` | `risk_level: str` | `risk_level` | `VARCHAR(20)` | Severity level |
| `riskLevelLabel` | `string` | `risk_level_label: str` | `risk_level_label` | `VARCHAR(100)` | Display label ("Critical Risk") |
| `riskLevelLabelUrdu`| `string` | `risk_level_label_urdu: str`| `risk_level_label_urdu`| `VARCHAR(100)` | Urdu display label |
| `explanation` | `string` | `explanation: str` | `explanation` | `TEXT` | Legal explanation |
| `explanationUrdu`| `string` | `explanation_urdu: str` | `explanation_urdu` | `TEXT` | Urdu explanation |
| `recommendation` | `string` | `recommendation: str` | `recommendation` | `TEXT` | Negotiation advice |
| `recommendationUrdu`| `string` | `recommendation_urdu: str` | `recommendation_urdu`| `TEXT` | Urdu advice |
| `impactMetric` | `string` | `impact_metric: str` | `impact_metric` | `VARCHAR(150)` | Financial exposure metric |
| `rawClauseSnippet`| `string` | `raw_clause_snippet: str` | `raw_clause_snippet` | `TEXT` | Verbatim contract quote |

---

## 7. Material Rates & BOQ Mapping (`src/types/cost.ts`)

### `MaterialRateItem`
| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | `name: str` | `name` | `VARCHAR(150)` | Material name |
| `nameUrdu` | `string` | `name_urdu: str` | `name_urdu` | `VARCHAR(150)` | Urdu name |
| `unit` | `string` | `unit: str` | `unit` | `VARCHAR(50)` | e.g. "per Ton" |
| `unitUrdu` | `string` | `unit_urdu: str` | `unit_urdu` | `VARCHAR(50)` | e.g. "فی ٹن" |
| `rate` | `string` | `rate: str` | `rate_pkr` | `NUMERIC(12,2)`| Formatted by Pydantic: `"PKR 248,500"` |
| `change` | `string` | `change: str` | `change_pct` | `NUMERIC(5,2)` | Formatted by Pydantic: `"+1.2%"` |
| `trend` | `"up" \| "down" \| "neutral"` | `trend: str` | `trend` | `VARCHAR(20)` | Price direction |
| `brand` | `string` | `brand: str` | `primary_brands` | `VARCHAR(255)` | Main Pakistani mills/brands |

---

## 8. Consulting Report Mapping (`src/types/report.ts` -> `ConsultingReport`)

| Frontend Field | Frontend Type | Backend Field | PostgreSQL Column | DB Type | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id: str` (from `code`) | `code` | `VARCHAR(50)` | Public report ID (`RPT-001`). DB PK is `id UUID`. |
| `title` | `string` | `title: str` | `title` | `VARCHAR(255)` | Dossier title |
| `titleUrdu` | `string` | `title_urdu: str` | `title_urdu` | `VARCHAR(255)` | Urdu title |
| `category` | `"compliance" \| "contract" \| "cost"` | `category: str` | `category` | `VARCHAR(50)` | Report domain |
| `categoryLabel` | `string` | `category_label: str` | `category_label` | `VARCHAR(100)` | Display label |
| `projectName` | `string` | `project_name: str` | *(Joined from `projects`)*| — | **Computed**: Fetched via relation |
| `projectNameUrdu`| `string` | `project_name_urdu: str` | *(Joined from `projects`)*| — | **Computed**: Fetched via relation |
| `date` | `string` | `date: str` | `created_at` | `TIMESTAMPTZ` | **Computed**: Formatted as `"January 15, 2025"` |
| `status` | `ReportStatus` | `status: str` | `status` | `VARCHAR(50)` | Status slug |
| `statusLabel` | `string` | `status_label: str` | `status_label` | `VARCHAR(100)` | Label ("Certified Compliant") |
| `statusLabelUrdu`| `string` | `status_label_urdu: str` | `status_label_urdu`| `VARCHAR(100)` | Urdu status label |
| `fileSize` | `string` | `file_size: str` | `file_size` | `VARCHAR(50)` | e.g. `"4.2 MB"` |
| `pageCount` | `number` | `page_count: int` | `page_count` | `INTEGER` | Dossier page length |
| `author` | `string` | `author: str` | `author` | `VARCHAR(150)` | Author attribution |
| `executiveSummary`| `string` | `executive_summary: str` | `executive_summary` | `TEXT` | Brief overview |
| `keyMetric` | `string` | `key_metric: str` | `key_metric` | `VARCHAR(150)` | Primary compliance/cost metric |
