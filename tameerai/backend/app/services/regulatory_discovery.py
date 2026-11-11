"""
TameerAI - Pakistan Statutory Regulatory Authority Discovery Service (Phase 03.3)

Provides authoritative catalog, geographic resolution, credibility tier classification,
and seed synchronization for Pakistan's national and sub-national building control authorities.
Supports both AsyncSession and sync Session.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.regulation import RegulatoryAuthority

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Master Inventory of Pakistan Regulatory Authorities (Statutory Baseline)
# ---------------------------------------------------------------------------

DEFAULT_PAKISTAN_AUTHORITIES: List[Dict[str, Any]] = [
    # Federal Authorities (Tier A: Statutory Legal Mandate)
    {
        "code": "PEC",
        "name": "Pakistan Engineering Council",
        "name_urdu": "پاکستان انجینئرنگ کونسل",
        "jurisdiction_level": "federal",
        "province": None,
        "city": "Islamabad",
        "official_website": "https://www.pec.org.pk",
        "regulatory_domain": "structural_and_licensing",
        "publication_channels": {
            "gazette": "The Gazette of Pakistan, Extraordinary",
            "enabling_act": "Pakistan Engineering Council Act, 1976 (Act No. V of 1976)",
            "bye_laws": "PEC Construction and Operation of Engineering Works Bye-laws 1987",
        },
        "credibility_tier": "tier_a_statutory",
        "verification_status": "verified",
    },
    {
        "code": "BCP_FED",
        "name": "Building Code of Pakistan / Ministry of Housing & Works",
        "name_urdu": "بلڈنگ کوڈ آف پاکستان",
        "jurisdiction_level": "federal",
        "province": None,
        "city": "Islamabad",
        "official_website": "https://www.housing.gov.pk",
        "regulatory_domain": "seismic_and_safety",
        "publication_channels": {
            "gazette": "The Gazette of Pakistan, Extraordinary",
            "statutory_mandate": "Formulated by PEC and notified by Ministry of Housing and Works",
            "editions": ["BCP-1986", "BCP-SP-2007", "BCP-EC-2011", "BCP-2021-DRAFT"],
        },
        "credibility_tier": "tier_a_statutory",
        "verification_status": "verified",
    },
    {
        "code": "ML_C",
        "name": "Military Lands and Cantonments Department",
        "name_urdu": "ملٹری لینڈز اینڈ کنٹونمنٹس ڈیپارٹمنٹ",
        "jurisdiction_level": "special_authority",
        "province": None,
        "city": "Rawalpindi",
        "official_website": "https://www.mlc.gov.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "The Gazette of Pakistan",
            "enabling_act": "Cantonments Act, 1924 (Act II of 1924)",
            "regulations": "Cantonment Building Bye-Laws",
        },
        "credibility_tier": "tier_a_statutory",
        "verification_status": "verified",
    },

    # Punjab Authorities (Tier B: Provincial Statutory & Municipal Development Authorities)
    {
        "code": "LDA",
        "name": "Lahore Development Authority",
        "name_urdu": "لاہور ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Punjab",
        "city": "Lahore",
        "official_website": "https://www.lda.gop.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Punjab Weekly Gazette",
            "enabling_act": "Lahore Development Authority Act, 1975 (Punjab Act XXX of 1975)",
            "primary_regulations": "LDA Building and Zoning Regulations 2020",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "RDA",
        "name": "Rawalpindi Development Authority",
        "name_urdu": "راولپنڈی ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Punjab",
        "city": "Rawalpindi",
        "official_website": "https://www.rda.gop.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Punjab Weekly Gazette",
            "enabling_act": "Punjab Development of Cities Act, 1976",
            "primary_regulations": "RDA Building and Zoning Regulations",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "FDA",
        "name": "Faisalabad Development Authority",
        "name_urdu": "فیصل آباد ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Punjab",
        "city": "Faisalabad",
        "official_website": "https://www.fda.gop.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Punjab Weekly Gazette",
            "enabling_act": "Punjab Development of Cities Act, 1976",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "MDA",
        "name": "Multan Development Authority",
        "name_urdu": "ملتان ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Punjab",
        "city": "Multan",
        "official_website": "https://www.mda.gop.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Punjab Weekly Gazette",
            "enabling_act": "Punjab Development of Cities Act, 1976",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "PLG_CD",
        "name": "Punjab Local Government & Community Development Department",
        "name_urdu": "محکمہ لوکل گورنمنٹ پنجاب",
        "jurisdiction_level": "provincial",
        "province": "Punjab",
        "city": "Lahore",
        "official_website": "https://www.lgcd.punjab.gov.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Punjab Weekly Gazette",
            "enabling_act": "Punjab Local Government Act, 2022",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },

    # Sindh Authorities
    {
        "code": "SBCA",
        "name": "Sindh Building Control Authority",
        "name_urdu": "سندھ بلڈنگ کنٹرول اتھارٹی",
        "jurisdiction_level": "provincial",
        "province": "Sindh",
        "city": "Karachi",
        "official_website": "https://www.sbca.gos.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "The Sindh Government Gazette",
            "enabling_act": "Sindh Building Control Ordinance, 1979",
            "primary_regulations": "Karachi Building & Town Planning Regulations 2002 (KBTPR 2002)",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "KDA",
        "name": "Karachi Development Authority",
        "name_urdu": "کراچی ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Sindh",
        "city": "Karachi",
        "official_website": "https://www.kda.gos.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "The Sindh Government Gazette",
            "enabling_act": "Karachi Development Authority Order, 1957",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },

    # Islamabad Capital Territory (ICT) Authorities
    {
        "code": "CDA",
        "name": "Capital Development Authority",
        "name_urdu": "کیپٹل ڈویلپمنٹ اتھارٹی اسلام آباد",
        "jurisdiction_level": "municipal",
        "province": "ICT",
        "city": "Islamabad",
        "official_website": "https://www.cda.gov.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "The Gazette of Pakistan, Extraordinary",
            "enabling_act": "Capital Development Authority Ordinance, 1960 (Ordinance XXIII of 1960)",
            "primary_regulations": "Islamabad Residential & Commercial Building Regulations 2020",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },

    # Khyber Pakhtunkhwa Authorities
    {
        "code": "PDA",
        "name": "Peshawar Development Authority",
        "name_urdu": "پشاور ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Khyber Pakhtunkhwa",
        "city": "Peshawar",
        "official_website": "https://www.pda.gkp.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Government Gazette Khyber Pakhtunkhwa",
            "enabling_act": "Khyber Pakhtunkhwa Urban Planning & Land Use Act, 2017",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },

    # Balochistan Authorities
    {
        "code": "QDA",
        "name": "Quetta Development Authority",
        "name_urdu": "کوئٹہ ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Balochistan",
        "city": "Quetta",
        "official_website": "https://www.qda.gob.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Balochistan Gazette",
            "enabling_act": "Quetta Development Authority Act, 1984",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
    {
        "code": "GDA_GW",
        "name": "Gwadar Development Authority",
        "name_urdu": "گوادر ڈویلپمنٹ اتھارٹی",
        "jurisdiction_level": "municipal",
        "province": "Balochistan",
        "city": "Gwadar",
        "official_website": "https://www.gda.gov.pk",
        "regulatory_domain": "planning_and_zoning",
        "publication_channels": {
            "gazette": "Balochistan Gazette",
            "enabling_act": "Gwadar Development Authority Act, 2003",
        },
        "credibility_tier": "tier_b_official_regulatory",
        "verification_status": "verified",
    },
]


class RegulatoryDiscoveryService:
    """
    Manages discovery, inventory, and location-based resolution of Pakistan regulatory authorities.
    Supports both AsyncSession and sync Session.
    """

    @classmethod
    async def seed_default_authorities_async(cls, db: AsyncSession) -> List[RegulatoryAuthority]:
        """
        Asynchronously seeds standard Pakistan authorities into the database if not present.
        """
        created = []
        for auth_dict in DEFAULT_PAKISTAN_AUTHORITIES:
            stmt = select(RegulatoryAuthority).where(RegulatoryAuthority.code == auth_dict["code"])
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if not existing:
                authority = RegulatoryAuthority(
                    id=uuid.uuid4(),
                    code=auth_dict["code"],
                    name=auth_dict["name"],
                    name_urdu=auth_dict.get("name_urdu"),
                    jurisdiction_level=auth_dict["jurisdiction_level"],
                    province=auth_dict.get("province"),
                    city=auth_dict.get("city"),
                    official_website=auth_dict["official_website"],
                    regulatory_domain=auth_dict["regulatory_domain"],
                    publication_channels=auth_dict.get("publication_channels"),
                    credibility_tier=auth_dict["credibility_tier"],
                    verification_status=auth_dict["verification_status"],
                    last_discovered_at=datetime.now(timezone.utc),
                )
                db.add(authority)
                created.append(authority)
        if created:
            await db.commit()
            for auth in created:
                await db.refresh(auth)
            logger.info("Seeded %d regulatory authorities into database", len(created))
        return created

    @classmethod
    def seed_default_authorities(cls, db: Session) -> List[RegulatoryAuthority]:
        """
        Synchronously seeds standard Pakistan authorities into the database if not present.
        """
        created = []
        for auth_dict in DEFAULT_PAKISTAN_AUTHORITIES:
            stmt = select(RegulatoryAuthority).where(RegulatoryAuthority.code == auth_dict["code"])
            existing = db.execute(stmt).scalars().first()
            if not existing:
                authority = RegulatoryAuthority(
                    id=uuid.uuid4(),
                    code=auth_dict["code"],
                    name=auth_dict["name"],
                    name_urdu=auth_dict.get("name_urdu"),
                    jurisdiction_level=auth_dict["jurisdiction_level"],
                    province=auth_dict.get("province"),
                    city=auth_dict.get("city"),
                    official_website=auth_dict["official_website"],
                    regulatory_domain=auth_dict["regulatory_domain"],
                    publication_channels=auth_dict.get("publication_channels"),
                    credibility_tier=auth_dict["credibility_tier"],
                    verification_status=auth_dict["verification_status"],
                    last_discovered_at=datetime.now(timezone.utc),
                )
                db.add(authority)
                created.append(authority)
        if created:
            db.commit()
            for auth in created:
                db.refresh(auth)
            logger.info("Seeded %d regulatory authorities into database", len(created))
        return created

    @classmethod
    async def get_authority_by_code_async(cls, db: AsyncSession, code: str) -> Optional[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority).where(RegulatoryAuthority.code == code.upper())
        res = await db.execute(stmt)
        return res.scalars().first()

    @classmethod
    def get_authority_by_code(cls, db: Session, code: str) -> Optional[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority).where(RegulatoryAuthority.code == code.upper())
        return db.execute(stmt).scalars().first()

    @classmethod
    async def list_authorities_async(
        cls,
        db: AsyncSession,
        jurisdiction_level: Optional[str] = None,
        credibility_tier: Optional[str] = None,
    ) -> List[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority)
        if jurisdiction_level:
            stmt = stmt.where(RegulatoryAuthority.jurisdiction_level == jurisdiction_level)
        if credibility_tier:
            stmt = stmt.where(RegulatoryAuthority.credibility_tier == credibility_tier)
        stmt = stmt.order_by(RegulatoryAuthority.code.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    def list_authorities(
        cls,
        db: Session,
        jurisdiction_level: Optional[str] = None,
        credibility_tier: Optional[str] = None,
    ) -> List[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority)
        if jurisdiction_level:
            stmt = stmt.where(RegulatoryAuthority.jurisdiction_level == jurisdiction_level)
        if credibility_tier:
            stmt = stmt.where(RegulatoryAuthority.credibility_tier == credibility_tier)
        stmt = stmt.order_by(RegulatoryAuthority.code.asc())
        return list(db.execute(stmt).scalars().all())

    @classmethod
    async def resolve_authorities_for_location_async(
        cls,
        db: AsyncSession,
        city: Optional[str] = None,
        province: Optional[str] = None,
    ) -> List[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority)
        res = await db.execute(stmt)
        all_authorities = list(res.scalars().all())
        return cls._filter_authorities_by_location(all_authorities, city, province)

    @classmethod
    def resolve_authorities_for_location(
        cls,
        db: Session,
        city: Optional[str] = None,
        province: Optional[str] = None,
    ) -> List[RegulatoryAuthority]:
        stmt = select(RegulatoryAuthority)
        all_authorities = list(db.execute(stmt).scalars().all())
        return cls._filter_authorities_by_location(all_authorities, city, province)

    @classmethod
    def _filter_authorities_by_location(
        cls,
        all_authorities: List[RegulatoryAuthority],
        city: Optional[str] = None,
        province: Optional[str] = None,
    ) -> List[RegulatoryAuthority]:
        city_clean = city.strip().title() if city else None
        prov_clean = province.strip().title() if province else None

        applicable: List[RegulatoryAuthority] = []

        city_province_map = {
            "Lahore": "Punjab",
            "Rawalpindi": "Punjab",
            "Faisalabad": "Punjab",
            "Multan": "Punjab",
            "Gujranwala": "Punjab",
            "Karachi": "Sindh",
            "Hyderabad": "Sindh",
            "Sukkur": "Sindh",
            "Islamabad": "ICT",
            "Peshawar": "Khyber Pakhtunkhwa",
            "Quetta": "Balochistan",
            "Gwadar": "Balochistan",
        }

        for auth in all_authorities:
            if auth.jurisdiction_level in ("federal", "special_authority"):
                applicable.append(auth)
                continue

            auth_prov = auth.province.strip().title() if auth.province else None
            auth_city = auth.city.strip().title() if auth.city else None

            # City match
            if city_clean and auth_city == city_clean:
                applicable.append(auth)
                continue

            # Province match
            if prov_clean and auth_prov == prov_clean:
                applicable.append(auth)
                continue

            # Inferred province match
            if city_clean:
                inferred_province = city_province_map.get(city_clean)
                if inferred_province and auth_prov == inferred_province:
                    applicable.append(auth)

        seen_ids = set()
        unique_applicable = []
        for a in applicable:
            if a.id not in seen_ids:
                seen_ids.add(a.id)
                unique_applicable.append(a)

        return unique_applicable
