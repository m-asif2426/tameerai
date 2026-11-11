"""
TameerAI - Base Source Adapter Interface for Material Rate Collection (Stage 2A)

Provides the extensible abstract base class that all data source adapters must inherit.
Defines mandatory lifecycle hooks:
- fetch_raw_data()
- parse_raw_data()
- normalize_records()
- validate_and_prepare()
- execute_collection_run()
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateSourceRun,
    MaterialRateObservation,
)
from app.services.material_rates.contracts import (
    CollectionSourceType,
    NormalizedObservationCandidate,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
    SourceRunSummary,
)
from app.services.material_rates.fingerprint import generate_observation_fingerprint
from app.services.material_rates.normalization import (
    NormalizationError,
    normalize_city,
    normalize_location,
    normalize_published_date,
    normalize_unit_and_price,
)

logger = logging.getLogger(__name__)


class BaseSourceAdapter(ABC):
    """
    Abstract Base Class for construction material pricing source adapters.
    Subclasses implement source-specific fetching and parsing while inheriting
    standardized normalization, SHA-256 fingerprinting, duplicate detection, and run accounting.
    """

    def __init__(
        self,
        *,
        source_code: str,
        source_name: str,
        source_type: CollectionSourceType,
        source_category: Optional[SourceCategory] = None,
        default_price_basis: PriceBasis = PriceBasis.RETAIL,
        base_url: Optional[str] = None,
        default_city: Optional[str] = None,
    ):
        self.source_code = source_code
        self.source_name = source_name
        self.source_type = source_type
        self.source_category = source_category
        self.default_price_basis = default_price_basis
        self.base_url = base_url
        self.default_city = default_city

    @abstractmethod
    async def fetch_raw_data(self, **kwargs) -> Any:
        """Fetches raw payload (JSON string, HTML content, CSV stream) from the source."""
        pass

    @abstractmethod
    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """Parses the raw source payload into intermediate RawSourceRecord objects."""
        pass

    def resolve_product(
        self,
        raw_name: str,
        category_hint: Optional[str],
        db_session: Any,
        preloaded_products: Optional[List[MaterialRateProduct]] = None,
    ) -> Optional[MaterialRateProduct]:
        """
        Resolves raw material text to an authoritative catalog MaterialRateProduct.
        Default implementation matches by code or canonical name substring.
        """
        clean_name = raw_name.strip().lower()

        if preloaded_products is not None:
            products = preloaded_products
        elif isinstance(db_session, Session):
            query = db_session.query(MaterialRateProduct).filter(MaterialRateProduct.is_active.is_(True))
            if category_hint:
                query = query.filter(MaterialRateProduct.category == category_hint.lower())
            products = query.all()
        else:
            products = []

        for p in products:
            if p.code.lower() == clean_name or p.canonical_name.lower() in clean_name or clean_name in p.canonical_name.lower():
                return p

        # Fallback to first active product in category if available
        if products:
            return products[0]
        return None

    def normalize_and_validate(
        self,
        record: RawSourceRecord,
        source: MaterialRateSource,
        db_session: Any,
        category_hint: Optional[str] = None,
        preloaded_products: Optional[List[MaterialRateProduct]] = None,
    ) -> Optional[NormalizedObservationCandidate]:
        """Standardizes a single raw record into a validated observation candidate."""
        try:
            # 1. Resolve product
            product = self.resolve_product(
                record.raw_material_name,
                category_hint,
                db_session,
                preloaded_products=preloaded_products,
            )
            if not product:
                logger.warning("Unresolved product catalog item for: '%s'", record.raw_material_name)
                return None

            # 2. Normalize location: preserve canonical_city, locality_or_district, quarry, river basin, and raw_location
            target_city = record.raw_city or self.default_city
            norm_loc = normalize_location(target_city)
            norm_city = norm_loc.canonical_city
            locality_or_district = norm_loc.locality_or_district
            raw_loc = norm_loc.raw_location

            # 3. Normalize price and measurement unit
            obs_price, obs_unit, norm_price, norm_unit = normalize_unit_and_price(
                record.raw_price, record.raw_unit
            )

            # 4. Normalize published date (returns None if undated to avoid inventing dates)
            pub_date = normalize_published_date(record.raw_published_date)

            # 5. Extract price basis, brand, grade, specification, and provenance
            price_basis = record.price_basis or self.default_price_basis
            brand = record.brand or (record.raw_metadata.get("brand") if record.raw_metadata else None)
            grade = record.grade or (record.raw_metadata.get("grade") if record.raw_metadata else None)
            spec = record.specification or (record.raw_metadata.get("specification") if record.raw_metadata else None)

            is_syndicated = bool(
                record.is_syndicated
                or record.republished_from
                or record.original_source_citation
            )

            # Secondary market publishers without independent corroboration are indicative
            if getattr(source, "source_category", None) == SourceCategory.SECONDARY_MARKET_PUBLISHER:
                verification_status = "indicative"
            elif is_syndicated:
                verification_status = "indicative"
            else:
                verification_status = "unverified"

            # 6. Compute raw payload hash
            payload_str = json.dumps(record.raw_metadata or {}, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            # Preserve location, provenance, timestamps, and classification details in observation metadata
            obs_metadata = dict(record.raw_metadata or {})
            obs_metadata["price_basis"] = price_basis.value if hasattr(price_basis, "value") else str(price_basis)
            obs_metadata["fetched_at"] = datetime.now(timezone.utc).isoformat()
            if brand:
                obs_metadata["brand"] = brand
            if grade:
                obs_metadata["grade"] = grade
            if spec:
                obs_metadata["specification"] = spec
            obs_metadata["provenance"] = {
                "is_syndicated": is_syndicated,
                "original_source_citation": record.original_source_citation,
                "republished_from": record.republished_from,
            }
            obs_metadata["location"] = {
                "raw_location": raw_loc,
                "canonical_city": norm_city,
                "locality_or_district": locality_or_district,
                "quarry_origin": norm_loc.quarry_origin,
                "river_basin": norm_loc.river_basin,
                "manufacturing_plant": norm_loc.manufacturing_plant,
            }

            return NormalizedObservationCandidate(
                source_id=source.id,
                product_id=product.id,
                category=product.category,
                canonical_name=product.canonical_name,
                city=norm_city,
                observed_price_pkr=obs_price,
                observed_unit=obs_unit,
                normalized_price_pkr=norm_price,
                normalized_unit=norm_unit,
                published_at=pub_date,
                verification_status=verification_status,
                raw_payload_hash=payload_hash,
                brand=brand,
                grade=grade,
                specification=spec,
                price_basis=price_basis,
                dealer_id=record.dealer_id,
                dealer_quote_id=record.dealer_quote_id,
                is_syndicated=is_syndicated,
                original_source_citation=record.original_source_citation,
                republished_from=record.republished_from,
                source_url=record.source_url or self.base_url,
                observation_metadata=obs_metadata,
            )
        except (NormalizationError, ValueError) as err:
            logger.warning("Record normalization rejected: %s", str(err))
            return None

    async def execute_run(
        self,
        db_session: Any,
        *,
        background_job_id: Optional[uuid.UUID] = None,
        category_hint: Optional[str] = None,
        **kwargs,
    ) -> SourceRunSummary:
        """
        Executes an end-to-end collection run:
        Fetch -> Parse -> Normalize -> Fingerprint -> Deduplicate -> Persist -> Audit Log.
        Compatible with both SQLAlchemy AsyncSession and sync Session.
        """
        # Ensure source exists in database and is committed so rollbacks during run do not erase it
        if isinstance(db_session, AsyncSession):
            res = await db_session.execute(select(MaterialRateSource).where(MaterialRateSource.code == self.source_code))
            source = res.scalar_one_or_none()
        else:
            source = db_session.query(MaterialRateSource).filter(MaterialRateSource.code == self.source_code).first()

        if not source:
            source = MaterialRateSource(
                code=self.source_code,
                name=self.source_name,
                source_type=self.source_type.value if hasattr(self.source_type, "value") else str(self.source_type),
                base_url=self.base_url,
                is_active=True,
            )
            db_session.add(source)
            if isinstance(db_session, AsyncSession):
                await db_session.commit()
                await db_session.refresh(source)
            else:
                db_session.commit()
                db_session.refresh(source)

        run_summary = SourceRunSummary(
            source_id=source.id,
            source_code=self.source_code,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        try:
            # 1. Fetch (Network I/O outside DB lock)
            raw_payload = await self.fetch_raw_data(**kwargs)

            # 2. Parse
            raw_records = self.parse_raw_data(raw_payload)
            run_summary.total_fetched = len(raw_records)

            # Preload active products for efficient lookup
            if isinstance(db_session, AsyncSession):
                stmt = select(MaterialRateProduct).where(MaterialRateProduct.is_active.is_(True))
                if category_hint:
                    stmt = stmt.where(MaterialRateProduct.category == category_hint.lower())
                prod_res = await db_session.execute(stmt)
                preloaded_products = list(prod_res.scalars().all())
            else:
                query = db_session.query(MaterialRateProduct).filter(MaterialRateProduct.is_active.is_(True))
                if category_hint:
                    query = query.filter(MaterialRateProduct.category == category_hint.lower())
                preloaded_products = query.all()

            # 3. Normalize & Deduplicate
            for raw_rec in raw_records:
                candidate = self.normalize_and_validate(
                    raw_rec,
                    source,
                    db_session,
                    category_hint=category_hint,
                    preloaded_products=preloaded_products,
                )
                if not candidate:
                    run_summary.rejected_count += 1
                    continue

                # Compute canonical SHA-256 fingerprint
                fingerprint = generate_observation_fingerprint(
                    source_id=candidate.source_id,
                    product_id=candidate.product_id,
                    city=candidate.city,
                    published_at=candidate.published_at,
                    normalized_price_pkr=candidate.normalized_price_pkr,
                    normalized_unit=candidate.normalized_unit,
                    dealer_id=candidate.dealer_id,
                )

                # Check duplicate in database
                if isinstance(db_session, AsyncSession):
                    dup_res = await db_session.execute(
                        select(MaterialRateObservation.id).where(
                            MaterialRateObservation.duplicate_fingerprint == fingerprint
                        )
                    )
                    existing_obs = dup_res.scalar_one_or_none()
                else:
                    existing_obs = (
                        db_session.query(MaterialRateObservation.id)
                        .filter(MaterialRateObservation.duplicate_fingerprint == fingerprint)
                        .first()
                    )

                if existing_obs:
                    run_summary.duplicate_count += 1
                    continue

                # Insert immutable observation
                obs = MaterialRateObservation(
                    source_id=candidate.source_id,
                    product_id=candidate.product_id,
                    dealer_quote_id=candidate.dealer_quote_id,
                    city=candidate.city,
                    observed_price_pkr=candidate.observed_price_pkr,
                    observed_unit=candidate.observed_unit,
                    normalized_price_pkr=candidate.normalized_price_pkr,
                    normalized_unit=candidate.normalized_unit,
                    published_at=candidate.published_at,
                    verification_status=candidate.verification_status,
                    duplicate_fingerprint=fingerprint,
                    background_job_id=background_job_id,
                    observation_metadata=candidate.observation_metadata,
                    source_url=candidate.source_url,
                )
                db_session.add(obs)
                run_summary.inserted_count += 1

            # Commit batch
            if isinstance(db_session, AsyncSession):
                await db_session.commit()
            else:
                db_session.commit()
            run_summary.status = "completed"

        except Exception as err:
            if isinstance(db_session, AsyncSession):
                await db_session.rollback()
            else:
                db_session.rollback()
            run_summary.status = "failed"
            # Sanitize error message (no secrets, safe summary)
            sanitized_err = f"{type(err).__name__}: {str(err)[:200]}"
            run_summary.error_message = sanitized_err
            logger.error("Collection run failed for source '%s': %s", self.source_code, sanitized_err)

        finally:
            run_summary.completed_at = datetime.now(timezone.utc)
            duration = None
            if run_summary.started_at and run_summary.completed_at:
                duration = Decimal(str(round((run_summary.completed_at - run_summary.started_at).total_seconds(), 2)))

            # Record telemetry in MaterialRateSourceRun
            source_run = MaterialRateSourceRun(
                source_id=source.id,
                background_job_id=background_job_id,
                status=run_summary.status,
                records_discovered=run_summary.total_fetched,
                records_accepted=run_summary.inserted_count,
                records_rejected=run_summary.rejected_count + run_summary.duplicate_count,
                error_summary=run_summary.error_message,
                duration_seconds=duration,
                started_at=run_summary.started_at,
                finished_at=run_summary.completed_at,
            )
            db_session.add(source_run)
            if isinstance(db_session, AsyncSession):
                await db_session.commit()
            else:
                db_session.commit()

        return run_summary
