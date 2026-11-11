"""
TameerAI - Identifier & Code Generation Utilities (Phase 01C.3)

Encapsulates dual-identifier logic and documentation for tenant-scoped public codes:
- Internal UUID primary keys for collision-free relational integrity, joins, and indexes.
- Tenant-scoped human-readable public codes (e.g. PRJ-001, DOC-01) matching frontend routes.
- Format validation and string representation helpers.

CONCURRENCY & IDENTIFIER ALLOCATION ARCHITECTURE (PHASE 02 SPECIFICATION):
--------------------------------------------------------------------------
1. Prohibited Anti-Patterns:
   - DO NOT USE `SELECT COUNT(*) + 1 ... FOR UPDATE`:
     PostgreSQL explicitly rejects `FOR UPDATE` on aggregate queries (raises SQL error).
     Furthermore, row counting fails when rows are deleted, producing reused numbers
     that collide with surviving records.
   - DO NOT USE `SELECT MAX(code) + 1`:
     Parsing integers out of alphanumeric strings requires table/index scans and creates
     concurrency race conditions under parallel transaction commits.

2. Future Database-Backed Atomic Counter Strategy (Phase 02 Service Layer):
   When project/document creation endpoints are implemented in Phase 02, identifier
   allocation will be backed by atomic, monotonic counter records:
   
   Example (Project Workspace Codes):
       CREATE TABLE project_counters (
           user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
           last_val INTEGER NOT NULL DEFAULT 0
       );

       -- Atomic increment with row-level lock on single tenant counter:
       INSERT INTO project_counters (user_id, last_val)
       VALUES (:user_id, 1)
       ON CONFLICT (user_id) DO UPDATE
       SET last_val = project_counters.last_val + 1
       RETURNING last_val;

   This provides:
   - Zero lock contention between different tenants/users.
   - Strict monotonic increments immune to deletions and rollbacks.
   - Instant O(1) integer generation without scanning application tables.

3. Database Uniqueness Constraints as Final Guard:
   - `projects`: `UNIQUE (user_id, code)`
   - `documents`: `UNIQUE (project_id, code)`
   These constraints serve as the database-enforced barrier guaranteeing zero duplicate codes.
"""

import re
from typing import Optional

# Regex patterns for public codes
PROJECT_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{3,6}$")  # e.g. PRJ-001, PRJ-0001
DOCUMENT_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{2,6}$")  # e.g. DOC-01, DOC-001
REPORT_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{3,6}$")    # e.g. RPT-001
FINDING_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{3,6}$")   # e.g. FIND-001, RULE-001
RISK_CODE_PATTERN = re.compile(r"^([A-Z]{2,6}-\d{3,6}|[a-z0-9\-]+)$")  # e.g. RISK-001, risk-delay
SESSION_CODE_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,50}$")  # e.g. session-1, chat-001
KNOWLEDGE_SHORT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{2,50}$")  # e.g. PBC_2021, FIDIC_RED_2017


def is_valid_project_code(code: str) -> bool:
    """Validates public project code format (e.g. 'PRJ-001')."""
    if not code:
        return False
    return bool(PROJECT_CODE_PATTERN.match(code.strip()))


def is_valid_document_code(code: str) -> bool:
    """Validates public document code format (e.g. 'DOC-01')."""
    if not code:
        return False
    return bool(DOCUMENT_CODE_PATTERN.match(code.strip()))


def is_valid_report_code(code: str) -> bool:
    """Validates public report code format (e.g. 'RPT-001')."""
    if not code:
        return False
    return bool(REPORT_CODE_PATTERN.match(code.strip()))


def is_valid_finding_code(code: str) -> bool:
    """Validates public finding code format (e.g. 'FIND-001')."""
    if not code:
        return False
    return bool(FINDING_CODE_PATTERN.match(code.strip()))


def format_project_code(sequence_num: int, prefix: str = "PRJ") -> str:
    """
    Formats a sequence number into a standard project code.
    Example: 1 -> 'PRJ-001', 42 -> 'PRJ-042', 105 -> 'PRJ-105'.
    """
    return f"{prefix}-{str(sequence_num).zfill(3)}"


def format_document_code(sequence_num: int, prefix: str = "DOC") -> str:
    """
    Formats a sequence number into a standard document code.
    Example: 1 -> 'DOC-01', 15 -> 'DOC-15'.
    """
    return f"{prefix}-{str(sequence_num).zfill(2)}"


def format_report_code(sequence_num: int, prefix: str = "RPT") -> str:
    """
    Formats a sequence number into a standard report code.
    Example: 1 -> 'RPT-001', 5 -> 'RPT-005'.
    """
    return f"{prefix}-{str(sequence_num).zfill(3)}"


def is_valid_session_code(code: str) -> bool:
    """Validates public chat session code format (e.g. 'session-1', 'chat-001')."""
    if not code:
        return False
    return bool(SESSION_CODE_PATTERN.match(code.strip()))


def is_valid_knowledge_short_code(code: str) -> bool:
    """Validates official knowledge source short code format (e.g. 'PBC_2021', 'LDA_2020')."""
    if not code:
        return False
    return bool(KNOWLEDGE_SHORT_CODE_PATTERN.match(code.strip()))

