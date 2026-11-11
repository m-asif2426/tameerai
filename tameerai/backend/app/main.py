from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup configuration and graceful database engine disposal on shutdown.
    """
    # Startup phase: No eager database connections opened during boot
    yield
    # Shutdown phase: Clean up connection pool
    await dispose_engine()


# FastAPI Application Factory / Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Construction Compliance & Cost Intelligence System",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure Development CORS Middleware for Next.js Frontend
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount Modular API Router (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


# =====================================================================
# Legacy Prototype Endpoints (Safely Unmounted for Production Security)
# =====================================================================

@app.get("/")
def home():
    return {
        "message": "TameerAI Backend is Running 🚀"
    }

# NOTE: Obsolete unauthenticated in-memory prototype routes (/projects)
# have been safely decommissioned per Phase 03.4E.2A.3 Task 4.
# All project operations must strictly use the authenticated, tenant-isolated
# endpoints at /api/v1/projects.
