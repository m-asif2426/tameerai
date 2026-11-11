import os
import re
import json

FRONTEND_APP_DIR = r"d:\new idea project\tameerai\frontend\src\app"

pages = [
    {"route": "/", "file": "page.tsx", "service": "costService.ts", "endpoint": "GET /api/v1/material-rates/snapshots"},
    {"route": "/auth/login", "file": "login/page.tsx", "service": "apiClient.ts", "endpoint": "POST /api/v1/auth/login"},
    {"route": "/auth/register", "file": "signup/page.tsx", "service": "apiClient.ts", "endpoint": "POST /api/v1/auth/register"},
    {"route": "/dashboard", "file": "dashboard/page.tsx", "service": "projectService.ts, costService.ts, safetyService.ts", "endpoint": "GET /projects, GET /material-rates/snapshots, POST /safety/evaluate"},
    {"route": "/dashboard/projects", "file": "dashboard/projects/page.tsx", "service": "projectService.ts", "endpoint": "GET /projects, POST /projects"},
    {"route": "/dashboard/projects/[id]", "file": "dashboard/projects/[id]/page.tsx", "service": "projectService.ts", "endpoint": "GET /projects/{id}, PATCH /projects/{id}"},
    {"route": "/dashboard/costs", "file": "dashboard/costs/page.tsx", "service": "costService.ts", "endpoint": "GET /material-rates/snapshots, GET /material-rates/history, GET /material-rates/compare"},
    {"route": "/dashboard/safety", "file": "dashboard/safety/page.tsx", "service": "safetyService.ts", "endpoint": "POST /safety/evaluate, POST /safety/verify-pec, POST /safety/sign-off"},
    {"route": "/dashboard/regulations", "file": "dashboard/regulations/page.tsx", "service": "regulationService.ts", "endpoint": "GET /regulations/authorities, POST /regulations/search"},
    {"route": "/dashboard/compliance", "file": "dashboard/compliance/page.tsx", "service": "complianceService.ts", "endpoint": "GET /compliance-audits, POST /compliance-audits"},
    {"route": "/dashboard/contracts", "file": "dashboard/contracts/page.tsx", "service": "contractService.ts", "endpoint": "GET /contract-analyses, POST /contract-analyses"},
    {"route": "/dashboard/ai-assistant", "file": "dashboard/ai-assistant/page.tsx", "service": "chatService.ts", "endpoint": "POST /chat/sessions, POST /chat/sessions/{id}/messages"},
    {"route": "/dashboard/reports", "file": "dashboard/reports/page.tsx", "service": "reportService.ts", "endpoint": "GET /reports, POST /reports"},
    {"route": "/dashboard/settings", "file": "dashboard/settings/page.tsx", "service": "apiClient.ts", "endpoint": "GET /users/me, PATCH /users/me/settings"},
]

def audit():
    print("=== TASK 7 FRONTEND DYNAMIC DATA AUDIT ===")
    for p in pages:
        full_path = os.path.join(FRONTEND_APP_DIR, p["file"])
        exists = os.path.exists(full_path)
        if not exists:
            print(f"MISSING: {full_path}")
            continue
        
        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()

        has_loading = "loading" in code.lower() or "skeleton" in code.lower() or "spinner" in code.lower() or "isloading" in code.lower()
        has_error = "error" in code.lower() or "failed" in code.lower() or "alert" in code.lower()
        has_empty = "empty" in code.lower() or "no " in code.lower() or "length === 0" in code or "0" in code
        has_mock = "dummy" in code.lower() or "mock" in code.lower() or "hardcoded" in code.lower()

        print(f"Page: {p['route']:26} | Service: {p['service']:35}")
        print(f"  Endpoint: {p['endpoint']}")
        print(f"  Loading State: {has_loading} | Error State: {has_error} | Empty State: {has_empty} | Mock Detected: {has_mock}")

if __name__ == "__main__":
    audit()

