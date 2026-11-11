from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    chat,
    compliance,
    contracts,
    costs,
    documents,
    health,
    jobs,
    material_rates,
    projects,
    regulations,
    reports,
    safety,
    users,
)

api_router = APIRouter()

# Mount health endpoint
api_router.include_router(health.router, tags=["Health"])

# Mount authentication endpoints (Phase 02A)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Mount user profile and settings endpoints (Phase 02B)
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Mount project workspace and collaboration endpoints (Phase 02C)
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

# Mount project document management endpoints (Phase 02D)
api_router.include_router(documents.router, prefix="/projects/{project_id}/documents", tags=["Documents"])

# Mount engineering intelligence endpoints (Phase 02E)
api_router.include_router(
    compliance.router,
    prefix="/projects/{project_id}/compliance-audits",
    tags=["Compliance Audits"],
)
api_router.include_router(
    contracts.router,
    prefix="/projects/{project_id}/contract-analyses",
    tags=["Contract Analyses"],
)
api_router.include_router(
    costs.router,
    prefix="/projects/{project_id}/boq-analyses",
    tags=["BOQ Analyses"],
)
api_router.include_router(
    material_rates.router,
    prefix="/material-rates",
    tags=["Material Rates"],
)
api_router.include_router(
    reports.router,
    prefix="/projects/{project_id}/reports",
    tags=["Consulting Reports"],
)

# Mount conversational AI assistant endpoints (Phase 02F)
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
)

# Mount structural safety advisory endpoints (Phase 03.2)
api_router.include_router(
    safety.router,
    prefix="/safety",
    tags=["Structural Safety"],
)

# Mount statutory regulatory knowledge base endpoints (Phase 03.3)
api_router.include_router(
    regulations.router,
    prefix="/regulations",
    tags=["Regulations"],
)

# Mount background job processing endpoints (Phase 02G)
api_router.include_router(
    jobs.router,
    prefix="/projects/{project_id}/jobs",
    tags=["Background Jobs"],
)

