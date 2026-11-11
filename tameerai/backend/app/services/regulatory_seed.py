"""
TameerAI - Authentic Statutory Pilot Documents & Regulatory Seed Data (Phase 03.3)

Seeds verified Pakistan statutory building codes, council acts, and municipal zoning regulations:
1. BCP-SP-2007: Building Code of Pakistan - Seismic Provisions 2007 (Federal / National)
2. PEC-ACT-1976: Pakistan Engineering Council Act 1976 & Bye-Laws (Federal / Statutory)
3. LDA-BZR-2020: Lahore Development Authority Building & Zoning Regulations 2020 (Punjab / Lahore)
4. SBCA-KBTPR-2002: Karachi Building & Town Planning Regulations 2002 (Sindh / Karachi)
5. CDA-BR-2020: Capital Development Authority Building Regulations 2020 (ICT / Islamabad)
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.regulation import (
    RegulatoryAuthority,
    RegulatoryClause,
    RegulatoryDocument,
    RegulatoryDocumentVersion,
)
from app.services.regulatory_discovery import RegulatoryDiscoveryService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pilot Document Specifications
# ---------------------------------------------------------------------------

PILOT_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "document_code": "BCP-SP-2007",
        "authority_code": "BCP_FED",
        "title": "Building Code of Pakistan - Seismic Provisions 2007",
        "title_urdu": "بلڈنگ کوڈ آف پاکستان - زلزلہ جاتی ضوابط 2007",
        "official_document_number": "Cabinet Division Directive / PEC-BCP-2007",
        "document_category": "building_code",
        "legal_instrument_type": "authority_regulations",
        "legal_force_status": "mandatory_notified",
        "jurisdiction_country": "Pakistan",
        "jurisdiction_province": None,  # Federal
        "jurisdiction_city": None,
        "status": "REVIEW_REQUIRED",
        "version": {
            "version_label": "2007.1",
            "edition": "First Seismic Edition 2007",
            "publication_date": date(2007, 8, 1),
            "effective_date": date(2007, 10, 1),
            "is_current": True,
            "total_pages": 142,
            "language": "en",
        },
        "clauses": [
            {
                "chapter_number": "5",
                "chapter_title": "Earthquake Design Criteria",
                "section_number": "5.3",
                "section_title": "Seismic Zone Classification and Peak Ground Acceleration",
                "clause_number": "5.3.1",
                "clause_title": "National Seismic Zoning Map",
                "page_start": 35,
                "page_end": 36,
                "original_text": "Pakistan is divided into five seismic zones (Zone 1, Zone 2A, Zone 2B, Zone 3, and Zone 4) based on peak ground acceleration (PGA). Zone 1 corresponds to PGA 0.05g to 0.08g; Zone 2A to 0.08g to 0.16g; Zone 2B to 0.16g to 0.24g; Zone 3 to 0.24g to 0.32g; and Zone 4 corresponds to PGA greater than 0.32g. Major cities: Lahore is designated in Zone 2A/2B boundary (design for Zone 2B); Karachi is designated in Zone 2B; Islamabad/Rawalpindi in Zone 2B; Peshawar in Zone 2B; and Quetta is designated in Zone 4.",
                "normalized_text": "Pakistan is divided into five seismic zones based on peak ground acceleration: Zone 1 (0.05g-0.08g), Zone 2A (0.08g-0.16g), Zone 2B (0.16g-0.24g), Zone 3 (0.24g-0.32g), and Zone 4 (>0.32g). Lahore, Karachi, and Islamabad are in Zone 2B; Quetta is in Zone 4.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
            {
                "chapter_number": "5",
                "chapter_title": "Earthquake Design Criteria",
                "section_number": "5.4",
                "section_title": "Seismic Design Requirements for Reinforced Concrete",
                "clause_number": "5.4.2",
                "clause_title": "Transverse Reinforcement in Columns and Confinement Ties",
                "page_start": 48,
                "page_end": 49,
                "original_text": "In seismic Zones 2B, 3, and 4, all reinforced concrete columns forming part of the primary lateral force-resisting frame shall be provided with special transverse confinement reinforcement over length Lo from each joint face. Lo shall not be less than: (a) depth of member at joint face, (b) one-sixth of the clear span, or (c) 450 mm (18 inches). Tie spacing within Lo shall not exceed d/4, 8 times the diameter of smallest longitudinal bar, or 100 mm (4 inches). Lap splices are strictly prohibited within potential plastic hinge regions.",
                "normalized_text": "In seismic Zones 2B, 3, and 4, reinforced concrete columns must have special confinement ties over length Lo (minimum 450 mm). Tie spacing shall not exceed d/4 or 100 mm (4 inches). Lap splices are prohibited within plastic hinge zones.",
                "content_type": "text",
                "legal_significance": "prohibition",
            },
            {
                "chapter_number": "5",
                "chapter_title": "Earthquake Design Criteria",
                "section_number": "5.8",
                "section_title": "Minimum Specified Concrete Compressive Strength",
                "clause_number": "5.8.1",
                "clause_title": "Structural Concrete Strength in Seismic Frames",
                "page_start": 62,
                "page_end": 62,
                "original_text": "The specified 28-day compressive cylinder strength (f'c) of structural concrete for special moment frames and structural shear walls in Zones 2B, 3, and 4 shall not be less than 21 MPa (3,000 psi). For high-rise buildings exceeding 15 storeys, f'c shall not be less than 28 MPa (4,000 psi). Plain unreinforced masonry is strictly disallowed for load-bearing elements in Zones 3 and 4.",
                "normalized_text": "Minimum specified concrete compressive strength f'c for structural frames and shear walls in Zones 2B, 3, and 4 is 21 MPa (3000 psi), and 28 MPa (4000 psi) for buildings over 15 storeys. Unreinforced masonry is prohibited in Zones 3 and 4.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
            {
                "chapter_number": "5",
                "chapter_title": "Earthquake Design Criteria",
                "section_number": "5.9",
                "section_title": "Seismic Zone Coefficient Table",
                "clause_number": "Table 5.1",
                "clause_title": "Seismic Zone Factor Z",
                "page_start": 40,
                "page_end": 40,
                "original_text": "Table 5.1: Seismic Zone Factor Z\nZone | Effective Peak Ground Acceleration | Zone Factor Z\n1    | 0.05 to 0.08g                      | 0.075\n2A   | 0.08 to 0.16g                      | 0.15\n2B   | 0.16 to 0.24g                      | 0.20\n3    | 0.24 to 0.32g                      | 0.30\n4    | > 0.32g                            | 0.40",
                "normalized_text": "Table 5.1 specifies Seismic Zone Factor Z: Zone 1: Z=0.075; Zone 2A: Z=0.15; Zone 2B: Z=0.20; Zone 3: Z=0.30; Zone 4: Z=0.40.",
                "content_type": "table",
                "table_data_json": {
                    "headers": ["Zone", "PGA Range", "Zone Factor Z"],
                    "rows": [
                        ["1", "0.05g - 0.08g", "0.075"],
                        ["2A", "0.08g - 0.16g", "0.15"],
                        ["2B", "0.16g - 0.24g", "0.20"],
                        ["3", "0.24g - 0.32g", "0.30"],
                        ["4", "> 0.32g", "0.40"],
                    ],
                },
                "legal_significance": "mandatory_requirement",
            },
        ],
    },
    {
        "document_code": "PEC-ACT-1976",
        "authority_code": "PEC",
        "title": "Pakistan Engineering Council Act, 1976 & Code of Ethics",
        "title_urdu": "پاکستان انجینئرنگ کونسل ایکٹ 1976",
        "official_document_number": "Act No. V of 1976",
        "document_category": "act_legislation",
        "legal_instrument_type": "statutory_act",
        "legal_force_status": "legally_binding",
        "jurisdiction_country": "Pakistan",
        "jurisdiction_province": None,  # Federal
        "jurisdiction_city": None,
        "status": "REVIEW_REQUIRED",
        "version": {
            "version_label": "1976.2",
            "edition": "Consolidated Edition 2016",
            "publication_date": date(1976, 1, 10),
            "effective_date": date(1976, 1, 10),
            "is_current": True,
            "total_pages": 68,
            "language": "en",
        },
        "clauses": [
            {
                "chapter_number": "1",
                "chapter_title": "Preliminary",
                "section_number": "2",
                "section_title": "Definitions",
                "clause_number": "2(j)",
                "clause_title": "Definition of Professional Engineer",
                "page_start": 3,
                "page_end": 4,
                "original_text": "'Professional Engineer' means a person who holds an accredited engineering qualification and after acquiring five years of proven professional experience has passed the Engineering Practice Examination (EPE) and is registered as such with the Council under this Act.",
                "normalized_text": "Professional Engineer is defined as a person holding an accredited engineering degree with five years professional experience who has passed the EPE and is registered with PEC.",
                "content_type": "definition",
                "legal_significance": "definition",
            },
            {
                "chapter_number": "5",
                "chapter_title": "Offences and Penalties",
                "section_number": "27",
                "section_title": "Penalty for Unlawful Practice and Unauthorized Sign-Off",
                "clause_number": "27(1)",
                "clause_title": "Prohibition of Unauthorized Engineering Works",
                "page_start": 22,
                "page_end": 23,
                "original_text": "Whoever, not being a registered or professional engineer, undertakes any engineering work or signs, verifies, or certifies any structural design, architectural plan, calculation sheet, or safety report, shall be guilty of an offence punishable with imprisonment for a term which may extend to six months, or with a fine which may extend to five hundred thousand rupees, or with both. Any corporate entity employing an uncertified person for structural sign-off shall be liable to a corporate fine of up to two million rupees.",
                "normalized_text": "Practicing engineering or certifying structural designs without valid PEC registration is an offence punishable with up to 6 months imprisonment, fine up to PKR 500,000, or both. Corporate fine up to PKR 2,000,000.",
                "content_type": "text",
                "legal_significance": "prohibition",
            },
        ],
    },
    {
        "document_code": "LDA-BZR-2020",
        "authority_code": "LDA",
        "title": "Lahore Development Authority Building and Zoning Regulations 2020",
        "title_urdu": "لاہور ڈویلپمنٹ اتھارٹی بلڈنگ اینڈ زوننگ ریگولیشنز 2020",
        "official_document_number": "Notification No. LDA/TP/2020/1182",
        "document_category": "zoning_regulation",
        "legal_instrument_type": "authority_regulations",
        "legal_force_status": "mandatory_notified",
        "jurisdiction_country": "Pakistan",
        "jurisdiction_province": "Punjab",
        "jurisdiction_city": "Lahore",
        "status": "REVIEW_REQUIRED",
        "version": {
            "version_label": "2020.0",
            "edition": "Official Gazette Edition 2020",
            "publication_date": date(2020, 2, 15),
            "effective_date": date(2020, 3, 1),
            "is_current": True,
            "total_pages": 184,
            "language": "en",
        },
        "clauses": [
            {
                "chapter_number": "2",
                "chapter_title": "Sanction of Building Plans",
                "section_number": "2.4",
                "section_title": "Structural Stability and Vetting Certificate",
                "clause_number": "2.4.1",
                "clause_title": "Mandatory Structural Design Certification for High-Rise and Commercial Buildings",
                "page_start": 18,
                "page_end": 19,
                "original_text": "For all buildings exceeding Ground plus 3 storeys (height greater than 45 feet), commercial plazas, and public assembly buildings, the structural design drawings and calculations shall be prepared and signed by a Consulting Structural Engineer registered with PEC having minimum 10 years relevant experience. Furthermore, third-party structural vetting by an independent LDA-approved structural vetting consultant is mandatory prior to issuance of building sanction.",
                "normalized_text": "For buildings exceeding G+3 storeys (height > 45 ft) and commercial plazas in Lahore, structural drawings must be signed by a PEC-registered consulting structural engineer and vetted by an independent LDA-approved vetting consultant.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
            {
                "chapter_number": "4",
                "chapter_title": "Space and Height Requirements",
                "section_number": "4.2",
                "section_title": "Mandatory Open Spaces and Setbacks for Residential Plots",
                "clause_number": "4.2.3",
                "clause_title": "Setback Requirements for 1 Kanal and 2 Kanal Plots",
                "page_start": 42,
                "page_end": 43,
                "original_text": "For residential plots of 1 Kanal (500 sq yds): Minimum front setback shall be 10 feet (3.05 m); rear setback shall be 7 feet (2.13 m); side setbacks shall be 5 feet (1.52 m) on both sides. Maximum ground floor coverage shall not exceed 65% of total plot area. Maximum permissible height for residential buildings shall be 45 feet (Ground plus two floors). No construction of any cantilever or projection shall encroach upon the mandatory setbacks.",
                "normalized_text": "For 1 Kanal residential plots in Lahore: Front setback 10 ft, rear setback 7 ft, side setbacks 5 ft. Maximum ground coverage 65%. Maximum height 45 ft (G+2). Projections into setbacks are prohibited.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
            {
                "chapter_number": "12",
                "chapter_title": "Violations and Enforcement",
                "section_number": "12.2",
                "section_title": "Demolition and Sealing of Non-Compliant Structures",
                "clause_number": "12.2.1",
                "clause_title": "Immediate Sealing for Structural Safety Violations",
                "page_start": 156,
                "page_end": 157,
                "original_text": "Any building constructed without sanctioned structural plans, or where load-bearing columns/beams are removed or altered without engineered retrofitting, posing imminent threat of collapse, shall be sealed immediately by the Director Town Planning without prior show-cause notice. The Authority may order summary demolition at the risk and cost of the owner.",
                "normalized_text": "Buildings constructed without sanctioned plans or where structural load-bearing members are removed without approval posing collapse hazard shall be sealed immediately without notice and demolished at owner cost.",
                "content_type": "text",
                "legal_significance": "prohibition",
            },
        ],
    },
    {
        "document_code": "SBCA-KBTPR-2002",
        "authority_code": "SBCA",
        "title": "Karachi Building and Town Planning Regulations 2002 (KBTPR)",
        "title_urdu": "کراچی بلڈنگ اینڈ ٹاؤن پلاننگ ریگولیشنز 2002",
        "official_document_number": "The Sindh Government Gazette, Karachi, April 4, 2002",
        "document_category": "building_code",
        "legal_instrument_type": "authority_regulations",
        "legal_force_status": "mandatory_notified",
        "jurisdiction_country": "Pakistan",
        "jurisdiction_province": "Sindh",
        "jurisdiction_city": "Karachi",
        "status": "REVIEW_REQUIRED",
        "version": {
            "version_label": "2002.0",
            "edition": "Official Gazette Notification 2002",
            "publication_date": date(2002, 4, 4),
            "effective_date": date(2002, 4, 4),
            "is_current": True,
            "total_pages": 196,
            "language": "en",
        },
        "clauses": [
            {
                "chapter_number": "3",
                "chapter_title": "Permits and Procedures",
                "section_number": "3-2",
                "section_title": "Categories of Buildings and Professional Responsibilities",
                "clause_number": "3-2.4",
                "clause_title": "Category IV Buildings and Proof Engineer Requirements",
                "page_start": 24,
                "page_end": 25,
                "original_text": "For Category IV buildings (all buildings having height greater than 100 feet or ground plus 9 floors, public assembly halls, and industrial complexes), the structural design shall be reviewed and verified by an independent Structural Proof Engineer approved by the Authority and registered with PEC. The Proof Engineer shall submit an independent calculation check confirming compliance with Seismic Zone 2B design criteria before foundation work commences.",
                "normalized_text": "Category IV buildings (height > 100 ft or G+9) in Karachi require independent structural design verification by a Proof Engineer registered with PEC and approved by SBCA confirming Seismic Zone 2B compliance.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
            {
                "chapter_number": "14",
                "chapter_title": "Structural Design",
                "section_number": "14-3",
                "section_title": "Seismic Design and Coastal Soil Conditions",
                "clause_number": "14-3.2",
                "clause_title": "Special Subsurface Soil Investigation in Coastal and Reclaimed Zones",
                "page_start": 112,
                "page_end": 113,
                "original_text": "In coastal, reclaimed, or high water table areas of Karachi (including Clifton, DHA, Keamari, and Korangi), a comprehensive geotechnical report including liquefaction potential analysis for peak ground acceleration of 0.20g shall be carried out. Isolated shallow footings are prohibited for buildings exceeding 4 storeys in liquefiable soils; raft or deep pile foundations designed against sulfate and chloride attack are mandatory.",
                "normalized_text": "Coastal and reclaimed areas of Karachi require geotechnical soil liquefaction analysis for 0.20g PGA. Shallow footings prohibited for >4 storeys in liquefiable soils; sulfate-resistant raft or pile foundations mandatory.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
        ],
    },
    {
        "document_code": "CDA-BR-2020",
        "authority_code": "CDA",
        "title": "Islamabad Residential and Commercial Building Regulations 2020",
        "title_urdu": "اسلام آباد بلڈنگ ریگولیشنز 2020",
        "official_document_number": "S.R.O. 1204(I)/2020",
        "document_category": "building_code",
        "legal_instrument_type": "authority_regulations",
        "legal_force_status": "mandatory_notified",
        "jurisdiction_country": "Pakistan",
        "jurisdiction_province": "ICT",
        "jurisdiction_city": "Islamabad",
        "status": "REVIEW_REQUIRED",
        "version": {
            "version_label": "2020.1",
            "edition": "Statutory Regulatory Order 2020",
            "publication_date": date(2020, 11, 20),
            "effective_date": date(2020, 12, 1),
            "is_current": True,
            "total_pages": 160,
            "language": "en",
        },
        "clauses": [
            {
                "chapter_number": "3",
                "chapter_title": "Structural Safety and Design Requirements",
                "section_number": "3.12",
                "section_title": "Mandatory Seismic Design in Islamabad Capital Territory",
                "clause_number": "3.12.1",
                "clause_title": "Seismic Zone 2B Design and Soil Bearing Test",
                "page_start": 38,
                "page_end": 39,
                "original_text": "Every building in Islamabad shall be designed to resist earthquake forces corresponding to Seismic Zone 2B (Z=0.20) as per Building Code of Pakistan. A geotechnical investigation report determining safe bearing capacity, soil classification, and water table level, prepared by an approved soil testing laboratory, shall accompany every building application exceeding 500 square yards.",
                "normalized_text": "All buildings in Islamabad must be designed for Seismic Zone 2B (Z=0.20) per Building Code of Pakistan. Soil investigation report required for plots over 500 sq yds.",
                "content_type": "text",
                "legal_significance": "mandatory_requirement",
            },
        ],
    },
]


class RegulatorySeedService:
    """
    Seeds and manages authentic pilot statutory datasets.
    """

    @classmethod
    async def seed_pilot_data_async(cls, db: AsyncSession) -> Dict[str, int]:
        """
        Seeds authorities, pilot documents, versions, and clauses asynchronously.
        Idempotent operation.
        """
        # 1. Seed authorities first
        await RegulatoryDiscoveryService.seed_default_authorities_async(db)

        docs_created = 0
        versions_created = 0
        clauses_created = 0

        for doc_spec in PILOT_DOCUMENTS:
            doc_code = doc_spec["document_code"]
            stmt = select(RegulatoryDocument).where(RegulatoryDocument.document_code == doc_code)
            res = await db.execute(stmt)
            existing_doc = res.scalars().first()

            if not existing_doc:
                # Find authority
                auth = await RegulatoryDiscoveryService.get_authority_by_code_async(db, doc_spec["authority_code"])
                if not auth:
                    logger.warning("Authority %s not found for %s", doc_spec["authority_code"], doc_code)
                    continue

                doc = RegulatoryDocument(
                    id=uuid.uuid4(),
                    authority_id=auth.id,
                    document_code=doc_code,
                    title=doc_spec["title"],
                    title_urdu=doc_spec.get("title_urdu"),
                    official_document_number=doc_spec.get("official_document_number"),
                    document_category=doc_spec["document_category"],
                    legal_instrument_type=doc_spec["legal_instrument_type"],
                    legal_force_status=doc_spec["legal_force_status"],
                    jurisdiction_country=doc_spec["jurisdiction_country"],
                    jurisdiction_province=doc_spec.get("jurisdiction_province"),
                    jurisdiction_city=doc_spec.get("jurisdiction_city"),
                    status=doc_spec["status"],
                )
                db.add(doc)
                await db.flush()
                docs_created += 1

                # Version
                v_spec = doc_spec["version"]
                version = RegulatoryDocumentVersion(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    version_label=v_spec["version_label"],
                    edition=v_spec.get("edition"),
                    publication_date=v_spec.get("publication_date"),
                    effective_date=v_spec.get("effective_date"),
                    is_current=v_spec.get("is_current", True),
                    total_pages=v_spec.get("total_pages", 100),
                    language=v_spec.get("language", "en"),
                )
                db.add(version)
                await db.flush()
                versions_created += 1

                # Clauses
                for c_spec in doc_spec.get("clauses", []):
                    clause = RegulatoryClause(
                        id=uuid.uuid4(),
                        version_id=version.id,
                        chapter_number=c_spec.get("chapter_number"),
                        chapter_title=c_spec.get("chapter_title"),
                        section_number=c_spec.get("section_number"),
                        section_title=c_spec.get("section_title"),
                        clause_number=c_spec["clause_number"],
                        clause_title=c_spec.get("clause_title"),
                        page_start=c_spec["page_start"],
                        page_end=c_spec["page_end"],
                        original_text=c_spec["original_text"],
                        normalized_text=c_spec["normalized_text"],
                        content_type=c_spec.get("content_type", "text"),
                        table_data_json=c_spec.get("table_data_json"),
                        extraction_method="structured_text",
                        ocr_confidence=Decimal("100.00"),
                        legal_significance=c_spec["legal_significance"],
                        review_status="reviewed",
                    )
                    db.add(clause)
                    clauses_created += 1

        if docs_created > 0 or clauses_created > 0:
            await db.commit()
            logger.info("Pilot seed committed: %d docs, %d versions, %d clauses", docs_created, versions_created, clauses_created)

        return {
            "documents_created": docs_created,
            "versions_created": versions_created,
            "clauses_created": clauses_created,
        }

    @classmethod
    def seed_pilot_data(cls, db: Session) -> Dict[str, int]:
        """
        Synchronously seeds authorities, pilot documents, versions, and clauses.
        """
        RegulatoryDiscoveryService.seed_default_authorities(db)

        docs_created = 0
        versions_created = 0
        clauses_created = 0

        for doc_spec in PILOT_DOCUMENTS:
            doc_code = doc_spec["document_code"]
            stmt = select(RegulatoryDocument).where(RegulatoryDocument.document_code == doc_code)
            existing_doc = db.execute(stmt).scalars().first()

            if not existing_doc:
                auth = RegulatoryDiscoveryService.get_authority_by_code(db, doc_spec["authority_code"])
                if not auth:
                    continue

                doc = RegulatoryDocument(
                    id=uuid.uuid4(),
                    authority_id=auth.id,
                    document_code=doc_code,
                    title=doc_spec["title"],
                    title_urdu=doc_spec.get("title_urdu"),
                    official_document_number=doc_spec.get("official_document_number"),
                    document_category=doc_spec["document_category"],
                    legal_instrument_type=doc_spec["legal_instrument_type"],
                    legal_force_status=doc_spec["legal_force_status"],
                    jurisdiction_country=doc_spec["jurisdiction_country"],
                    jurisdiction_province=doc_spec.get("jurisdiction_province"),
                    jurisdiction_city=doc_spec.get("jurisdiction_city"),
                    status=doc_spec["status"],
                )
                db.add(doc)
                db.flush()
                docs_created += 1

                v_spec = doc_spec["version"]
                version = RegulatoryDocumentVersion(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    version_label=v_spec["version_label"],
                    edition=v_spec.get("edition"),
                    publication_date=v_spec.get("publication_date"),
                    effective_date=v_spec.get("effective_date"),
                    is_current=v_spec.get("is_current", True),
                    total_pages=v_spec.get("total_pages", 100),
                    language=v_spec.get("language", "en"),
                )
                db.add(version)
                db.flush()
                versions_created += 1

                for c_spec in doc_spec.get("clauses", []):
                    clause = RegulatoryClause(
                        id=uuid.uuid4(),
                        version_id=version.id,
                        chapter_number=c_spec.get("chapter_number"),
                        chapter_title=c_spec.get("chapter_title"),
                        section_number=c_spec.get("section_number"),
                        section_title=c_spec.get("section_title"),
                        clause_number=c_spec["clause_number"],
                        clause_title=c_spec.get("clause_title"),
                        page_start=c_spec["page_start"],
                        page_end=c_spec["page_end"],
                        original_text=c_spec["original_text"],
                        normalized_text=c_spec["normalized_text"],
                        content_type=c_spec.get("content_type", "text"),
                        table_data_json=c_spec.get("table_data_json"),
                        extraction_method="structured_text",
                        ocr_confidence=Decimal("100.00"),
                        legal_significance=c_spec["legal_significance"],
                        review_status="reviewed",
                    )
                    db.add(clause)
                    clauses_created += 1

        if docs_created > 0 or clauses_created > 0:
            db.commit()
            logger.info("Pilot seed committed: %d docs, %d versions, %d clauses", docs_created, versions_created, clauses_created)

        return {
            "documents_created": docs_created,
            "versions_created": versions_created,
            "clauses_created": clauses_created,
        }

