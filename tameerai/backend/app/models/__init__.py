"""
TameerAI - Database Models Package
Exports all SQLAlchemy models across Identity, Workspace, and Engineering Intelligence domains.
"""

from app.models.user import User, UserSettings, UserSession
from app.models.project import Project, ProjectMember, ProjectActivity
from app.models.document import Document
from app.models.compliance import ComplianceAudit, ComplianceFinding
from app.models.contract import ContractAnalysis, ContractRiskCard
from app.models.cost import MaterialRate, BOQAnalysis, BOQItem
from app.models.report import Report
from app.models.chat import ChatSession, ChatMessage
from app.models.knowledge import KnowledgeSource, DocumentChunk
from app.models.job import BackgroundJob, JobStatus, JobType
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateVerificationEvent,
    MaterialRateSourceRun,
)
from app.models.regulation import (
    RegulatoryAuthority,
    RegulatoryDocument,
    RegulatoryDocumentVersion,
    RegulatoryClause,
    RegulatoryAmendment,
    RegulatoryIngestionJob,
    RegulatoryReviewRecord,
)

__all__ = [
    # Identity Models (Phase 01C.2)
    "User",
    "UserSettings",
    "UserSession",
    # Project & Document Models (Phase 01C.3)
    "Project",
    "ProjectMember",
    "ProjectActivity",
    "Document",
    # Engineering Intelligence Models (Phase 01C.4)
    "ComplianceAudit",
    "ComplianceFinding",
    "ContractAnalysis",
    "ContractRiskCard",
    "MaterialRate",
    "BOQAnalysis",
    "BOQItem",
    "Report",
    # Conversational AI & RAG Models (Phase 01C.5)
    "ChatSession",
    "ChatMessage",
    "KnowledgeSource",
    "DocumentChunk",
    # Background Processing Models (Phase 02G)
    "BackgroundJob",
    "JobStatus",
    "JobType",
    # Material Rate Intelligence Models (Stage 1 / Phase 03H)
    "MaterialRateProduct",
    "MaterialRateSource",
    "MaterialRateDealer",
    "MaterialRateDealerQuote",
    "MaterialRateObservation",
    "MaterialRateVerificationEvent",
    "MaterialRateSourceRun",
    # Statutory Regulatory Knowledge Base Models (Phase 03.3)
    "RegulatoryAuthority",
    "RegulatoryDocument",
    "RegulatoryDocumentVersion",
    "RegulatoryClause",
    "RegulatoryAmendment",
    "RegulatoryIngestionJob",
    "RegulatoryReviewRecord",
]
