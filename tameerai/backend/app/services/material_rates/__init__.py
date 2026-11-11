"""
TameerAI - Material Rates Service Package
"""

from app.services.material_rates.fingerprint import (
    generate_observation_fingerprint,
    FINGERPRINT_VERSION_V1,
)
from app.services.material_rates.contracts import (
    CollectionSourceType,
    SourceCategory,
    SourceOperationalStatus,
    PriceBasis,
    NormalizedCategory,
    RawSourceRecord,
    NormalizedObservationCandidate,
    SourceRunSummary,
)
from app.services.material_rates.registry import (
    NationalSourceRegistry,
    SourceRegistryEntry,
    national_registry,
)

__all__ = [
    "generate_observation_fingerprint",
    "FINGERPRINT_VERSION_V1",
    "CollectionSourceType",
    "SourceCategory",
    "SourceOperationalStatus",
    "PriceBasis",
    "NormalizedCategory",
    "RawSourceRecord",
    "NormalizedObservationCandidate",
    "SourceRunSummary",
    "NationalSourceRegistry",
    "SourceRegistryEntry",
    "national_registry",
]

