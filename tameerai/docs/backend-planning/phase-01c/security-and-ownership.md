# TameerAI — Security, Ownership & Tenant Isolation Model (Phase 01C.1)

**Project:** TameerAI Construction Compliance & Cost Intelligence  
**Core Strategy:** Application-Enforced Multi-Tenancy with PostgreSQL Relational Integrity  
**Revision:** Post-Audit Corrected Version (Role Hierarchy & RAG Isolation Finalized)

---

## 1. Architectural Security Philosophy

In the TameerAI architecture, **FastAPI is the authoritative backend gatekeeper**.

### Why Not Rely Purely on Supabase RLS?
1. **Frontend Does Not Connect Directly to PostgreSQL:** The Next.js frontend interacts exclusively with FastAPI via REST endpoints (`/api/v1/*`).
2. **Centralized Business Rules:** Engineering validation, PDF report synthesis, and LangGraph multi-agent RAG pipelines require server-side orchestration that cannot execute inside database triggers.
3. **Defense-in-Depth:**
   - **Layer 1 (Application Layer):** FastAPI OAuth2 / JWT dependency (`get_current_user`) injects the authenticated `User` context into every route.
   - **Layer 2 (Query Layer):** Every repository query explicitly includes tenant filtering (`WHERE projects.user_id = current_user.id OR project_members.user_id = current_user.id`).
   - **Layer 3 (Database Layer):** Foreign key constraints with explicit `ON DELETE CASCADE` or `ON DELETE RESTRICT`, unique scoped constraints, and check constraints prevent orphaned records or cross-project data leakage.

---

## 2. Project Role Hierarchy & Permission Matrix

A project is owned by a single creator (`projects.user_id`), but multi-disciplinary collaboration is supported through `project_members`. The system defines five strictly delineated roles:

1. **Owner (`owner`):** Full administrative and engineering control over the project workspace.
2. **Lead Engineer (`lead_engineer`):** Technical authority. Can trigger compliance audits, upload blueprints, run BOQ and contract risk analyses, and generate official reports.
3. **Architect (`architect`):** Design specialist. Can upload architectural/structural drawings and review/annotate compliance findings.
4. **Contractor (`contractor`):** Field execution specialist. Can view BOQ items, material rates, and compliance directives. Read-only on legal contracts.
5. **Viewer (`viewer`):** Read-only stakeholder (e.g. client, financial auditor). Can view dashboards, findings, and generated PDF reports.

### Detailed Permission Matrix

| Capability / Action | Owner | Lead Engineer | Architect | Contractor | Viewer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Edit Project Metadata** (Budget, City, Status) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Delete Project Workspace** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Manage Project Members** (Invite, Revoke) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Upload Documents / Blueprints** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Delete Documents** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Trigger Compliance Audit** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Annotate Findings / CAD Pins** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Trigger Contract Risk Analysis** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Trigger BOQ Cost Analysis** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Modify Custom Material Rates** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Generate Formal Consulting Reports** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **View Project Dashboard & Reports** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Participate in Project AI Chat** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 3. RAG Multi-Tenant Vector Scope Isolation

In an AI-powered construction intelligence system, regulatory knowledge (e.g., Pakistan Building Code 2021, FIDIC Rainbow Suite) is globally shared, whereas private architectural blueprints, commercial contracts, and proprietary BOQ schedules must remain strictly confidential to authorized project collaborators.

### 3.1 Database-Level Scope Invariant
The `document_chunks` table enforces this separation using an explicit PostgreSQL CHECK constraint:

```sql
CONSTRAINT ck_document_chunks_scope CHECK (
    (
        knowledge_source_id IS NOT NULL 
        AND project_id IS NULL 
        AND project_document_id IS NULL
    )
    OR
    (
        knowledge_source_id IS NULL 
        AND project_id IS NOT NULL 
        AND project_document_id IS NOT NULL
    )
)
```

- **Global Chunks:** Originate from official regulatory sources (`knowledge_source_id IS NOT NULL`). They are never tied to any specific project or user document.
- **Private Chunks:** Originate strictly from a verified project document (`project_id IS NOT NULL`, `project_document_id IS NOT NULL`). They cannot exist without a parent project.
- **Mutual Exclusivity:** A chunk can **never** be both global and project-specific.

### 3.2 Retrieval Query Isolation Guarantee
During LangGraph / LangChain vector similarity search, the embedding retrieval query must strictly isolate project boundaries:

```python
# Secure RAG Vector Search Filter
async def query_vector_store(
    query_embedding: list[float],
    project_id: UUID | None,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    if project_id:
        # Search global regulations PLUS this project's private blueprints
        scope_filter = or_(
            DocumentChunk.knowledge_source_id.is_not(None),
            DocumentChunk.project_id == project_id
        )
    else:
        # General query: Search strictly global regulatory documents
        scope_filter = DocumentChunk.knowledge_source_id.is_not(None)

    query = (
        select(DocumentChunk)
        .where(scope_filter)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return await db.scalars(query)
```

This ensures that under no circumstances can documents or chunks belonging to **Project A** ever be retrieved, cited, or exposed in an audit or chat session belonging to **Project B**.

---

## 4. Resource Ownership Hierarchy & Lookup Patterns

```
[ User (Account) ]
       │
       ├──────────────────────────────────────────────┐
       │ (1:N Owns)                                   │ (1:N Owns)
       ▼                                              ▼
   [ Projects ]                                 [ Chat Sessions ]
       │                                              │
       ├──────────────┬──────────────┐                ▼
       ▼              ▼              ▼         [ Chat Messages ]
   [ Documents ]  [ Audits ]     [ Reports ]
       │              │
       ▼              ▼
[ Private Doc   [ Compliance
   Chunks ]       Findings ]
```

### Polymorphic FastAPI Identifier Dependency
FastAPI dependencies transparently support both internal UUIDs and human-readable codes (e.g. `PRJ-001`):

```python
async def get_project_for_user(
    identifier: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    # Check if identifier is a valid UUID or a code
    is_uuid = False
    try:
        val = uuid.UUID(identifier)
        is_uuid = True
    except ValueError:
        pass

    if is_uuid:
        condition = (Project.id == val)
    else:
        condition = (Project.code == identifier)

    query = (
        select(Project)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .where(
            condition,
            or_(
                Project.user_id == current_user.id,
                ProjectMember.user_id == current_user.id,
            ),
        )
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it.",
        )
    return project
```

---

## 5. Secret Storage & Password Security

- **User Passwords:** Hashed with `bcrypt` (Passlib wrapper) using salt rounds of 12. Plaintext passwords are never stored, logged, or serialized into response models.
- **Tokens:** Refresh token hashes (`refresh_token_hash`) are stored in `user_sessions` for revocation support; raw JWT tokens are never persisted in the database.
- **Connection Strings & Keys:** Stored strictly in `.env`, injected via Pydantic Settings, and masked with `***` in error reports.
