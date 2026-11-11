"""
TameerAI - Grounded Evidence & Technical Response Policy (Phase 03G Stage B3.1)

Decouples internal grounding evaluation into 4 orthogonal dimensions:
1. Evidence Status: VERIFIED, PARTIALLY_SUPPORTED, INSUFFICIENT, UNVERIFIED
2. Calculation Status: VERIFIED, MISMATCH, NOT_APPLICABLE, NOT_VERIFIABLE
3. Regulatory Status: VERIFIED_REFERENCE, UNVERIFIED_REFERENCE, INTERPRETATION_UNVERIFIED, NOT_APPLICABLE
4. Citation Status: VALID, INVALID, PARTIALLY_SUPPORTED, RELEVANCE_UNVERIFIED

Maintains 100% backward compatibility with 5-Tier EvidenceTier for legacy callers.
Generates localized, natural disclosure notices in English, Pakistani Roman Urdu, and Urdu script.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.contracts.retrieval import RetrievedChunk
from app.ai.contracts.validation import (
    CitationStatus,
    CitationValidationReport,
    ClaimRelevanceStatus,
    CalculationStatus,
    EvidenceStatus,
    RegulatoryStatus,
    ValidationStatus,
)
from app.ai.guardrails.context_engine import ConstructionContext, ResponseStrategy, RiskLevel
from app.ai.guardrails.intent import ConstructionIntent
from app.ai.validation.citation import CitationValidator
from app.ai.validation.technical_accuracy import (
    EngineeringFormulaVerifier,
    MaterialRateAuditReport,
    MaterialRateReliabilityVerifier,
    TechnicalAuditItem,
    UngroundedClaimDetector,
    UnitConsistencyAuditor,
)


class EvidenceTier(str, Enum):
    """5-Tier Grounding Evaluation for Construction Answers (Backward Compatible)."""
    VERIFIED_ANSWER = "verified_answer"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CALCULATION_VERIFIED = "calculation_verified"
    REGULATORY_UNVERIFIED = "regulatory_unverified"


class GroundedResponseEvaluation(BaseModel):
    """Overall evidence-grounding scorecard with 4 independent verification dimensions."""
    evidence_status: EvidenceStatus
    calculation_status: CalculationStatus
    regulatory_status: RegulatoryStatus
    citation_status: CitationStatus
    tier: EvidenceTier
    is_grounded: bool
    citation_report: Optional[CitationValidationReport] = None
    calculation_audits: List[TechnicalAuditItem] = Field(default_factory=list)
    ungrounded_claims: List[TechnicalAuditItem] = Field(default_factory=list)
    unit_issues: List[TechnicalAuditItem] = Field(default_factory=list)
    rate_report: Optional[MaterialRateAuditReport] = None
    regulatory_discrepancies: List[str] = Field(default_factory=list)
    disclosure_note: Optional[str] = None
    annotated_answer: str


class GroundedResponsePolicy:
    """
    Intelligent evidence-aware response policy engine.
    Separates documentary evidence, deterministic calculations, citations, and regulatory interpretations.
    """

    @classmethod
    def evaluate_grounding(
        cls,
        query: str,
        response_text: str,
        context: Optional[ConstructionContext],
        retrieved_chunks: List[RetrievedChunk],
        citations: List[Dict[str, Any]],
        project_id: Optional[UUID] = None,
        available_rates: Optional[List[Any]] = None,
        language: str = "en",
    ) -> GroundedResponseEvaluation:
        """
        Evaluates technical grounding across 4 independent dimensions:
        - Evidence status
        - Calculation status
        - Regulatory status
        - Citation status
        And maps to legacy EvidenceTier for backward compatibility.
        """
        # 1. Validate structured citations if present
        citation_validator = CitationValidator()
        citation_report: Optional[CitationValidationReport] = None
        if citations:
            citation_report = citation_validator.validate_citations(
                citations=citations,
                evidence_chunks=retrieved_chunks,
                project_id=project_id,
            )

        # 2. Audit inline regulatory references quoted in text against retrieved chunks
        inline_reg_items = CitationValidator.validate_inline_regulatory_references(
            text=response_text,
            evidence_chunks=retrieved_chunks,
        )
        unverified_reg_clauses: List[str] = [
            item.citation_text for item in inline_reg_items if item.status == ValidationStatus.INVALID_CLAUSE
        ]
        has_unverified_interpretation = any(
            item.claim_relevance_status == ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED
            for item in inline_reg_items
        )

        # 3. Mathematical & formula cross-checks
        calc_audits = EngineeringFormulaVerifier.audit_response_calculations(response_text)
        unit_issues = UnitConsistencyAuditor.audit_unit_consistency(response_text)

        # 4. Ungrounded high-impact claims
        all_evidence_text = "\n".join(c.content for c in retrieved_chunks)
        ungrounded = UngroundedClaimDetector.detect_ungrounded_claims(
            text=response_text,
            has_verified_evidence=bool(retrieved_chunks),
            evidence_text=all_evidence_text,
        )

        # 5. Material rate verification
        rate_report = MaterialRateReliabilityVerifier.audit_material_rates(
            text=response_text,
            available_rates=available_rates,
        )

        # --------------------------------------------------------------------
        # 6. EVALUATE 4 INDEPENDENT VERIFICATION DIMENSIONS
        # --------------------------------------------------------------------

        # A. CITATION STATUS
        if citation_report and citation_report.citation_status:
            cit_status = citation_report.citation_status
        elif not citations:
            cit_status = CitationStatus.VALID
        else:
            cit_status = CitationStatus.VALID

        # B. CALCULATION STATUS
        has_calc_intent = context is not None and context.intent in (
            ConstructionIntent.CALCULATION,
            ConstructionIntent.QUANTITY_ESTIMATE,
        )
        if not calc_audits and not unit_issues:
            calc_status = CalculationStatus.NOT_APPLICABLE
        elif unit_issues or any(ca.calculation_status == CalculationStatus.NOT_VERIFIABLE for ca in calc_audits):
            calc_status = CalculationStatus.NOT_VERIFIABLE
        elif any(ca.calculation_status == CalculationStatus.MISMATCH or not ca.is_valid for ca in calc_audits):
            calc_status = CalculationStatus.MISMATCH
        elif any(ca.calculation_status == CalculationStatus.VERIFIED or ca.is_valid for ca in calc_audits):
            calc_status = CalculationStatus.VERIFIED
        else:
            calc_status = CalculationStatus.NOT_APPLICABLE

        # C. REGULATORY STATUS
        is_compliance_intent = context is not None and context.intent == ConstructionIntent.COMPLIANCE
        has_inline_regs = bool(inline_reg_items)
        has_reg_citations = any(
            any(cit.get("source_code", "").upper().startswith(p) for p in ["PBC", "LDA", "CDA", "SBCA", "KDA", "PEC", "FIDIC"])
            for cit in citations
        )

        unverified_compliance_pattern = re.compile(
            r"\b(?:guaranteed|100%|strictly|fully)\s*(?:compliant|approved|legal|certified)\b|"
            r"\b(?:meets\s+all\s+legal\s+requirements|approved\s+by\s+authority|guaranteed\s+approval)\b|"
            r"\b(?:statutory\s+approval|statutory\s+certification)\b|"
            r"\blegal\s+compliance\s+is\s+confirmed\b",
            re.IGNORECASE,
        )
        has_direct_compliance_claim = bool(unverified_compliance_pattern.search(response_text))

        if has_direct_compliance_claim or has_unverified_interpretation:
            reg_status = RegulatoryStatus.INTERPRETATION_UNVERIFIED
        elif not (is_compliance_intent or has_inline_regs or has_reg_citations):
            reg_status = RegulatoryStatus.NOT_APPLICABLE
        elif unverified_reg_clauses or (is_compliance_intent and not retrieved_chunks):
            reg_status = RegulatoryStatus.UNVERIFIED_REFERENCE
        else:
            reg_status = RegulatoryStatus.VERIFIED_REFERENCE

        # D. EVIDENCE STATUS
        if not retrieved_chunks:
            ev_status = EvidenceStatus.INSUFFICIENT
        else:
            has_unsupported_citations = (citation_report and citation_report.unsupported_citations > 0)
            has_ungrounded = len(ungrounded) > 0
            has_unreliable_rates = (rate_report is not None and rate_report.has_price_claims and not rate_report.is_reliable)
            has_partial_citations = bool(citation_report and any(i.claim_relevance_status == ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED for i in citation_report.items))

            if (
                has_unsupported_citations
                or has_ungrounded
                or has_unreliable_rates
                or has_partial_citations
                or reg_status == RegulatoryStatus.INTERPRETATION_UNVERIFIED
            ):
                ev_status = EvidenceStatus.PARTIALLY_SUPPORTED
            else:
                ev_status = EvidenceStatus.VERIFIED

        # --------------------------------------------------------------------
        # 7. DERIVE BACKWARD-COMPATIBLE EVIDENCE TIER & DISCLOSURE
        # --------------------------------------------------------------------
        tier = EvidenceTier.VERIFIED_ANSWER
        is_grounded = True
        disclosure_note: Optional[str] = None

        if reg_status == RegulatoryStatus.UNVERIFIED_REFERENCE:
            tier = EvidenceTier.REGULATORY_UNVERIFIED
            is_grounded = False
            disclosure_note = cls.get_regulatory_unverified_note(language)

        elif calc_status == CalculationStatus.VERIFIED and (has_calc_intent or not retrieved_chunks):
            tier = EvidenceTier.CALCULATION_VERIFIED
            is_grounded = True
            if not retrieved_chunks:
                disclosure_note = cls.get_calculation_verified_no_evidence_note(language)
            else:
                disclosure_note = cls.get_calculation_verified_note(language)

        elif ev_status == EvidenceStatus.INSUFFICIENT:
            tier = EvidenceTier.INSUFFICIENT_EVIDENCE
            is_grounded = False
            disclosure_note = cls.get_insufficient_evidence_note(language)

        elif ev_status == EvidenceStatus.PARTIALLY_SUPPORTED or reg_status == RegulatoryStatus.INTERPRETATION_UNVERIFIED:
            tier = EvidenceTier.PARTIALLY_SUPPORTED
            is_grounded = True
            disclosure_note = cls.get_partially_supported_note(language)

        else:
            tier = EvidenceTier.VERIFIED_ANSWER
            is_grounded = True
            disclosure_note = None

        # Build annotated answer
        annotated_answer = response_text
        if disclosure_note and disclosure_note.strip() not in annotated_answer:
            annotated_answer = response_text.rstrip() + "\n\n" + disclosure_note.strip()

        # Calculation alert for mismatches
        if calc_status == CalculationStatus.MISMATCH:
            err_notes = [ca.explanation for ca in calc_audits if not ca.is_valid]
            err_block = "\n\n⚠️ **Calculation Alert:** " + " ".join(err_notes)
            annotated_answer += err_block
        elif calc_status == CalculationStatus.NOT_VERIFIABLE:
            unv_calc_note = cls.get_unverified_calculation_note(language)
            if unv_calc_note not in annotated_answer:
                annotated_answer += "\n\n" + unv_calc_note

        # Dimensional alert for incompatible units
        if unit_issues:
            unit_notes = [u.explanation for u in unit_issues]
            unit_block = "\n\n⚠️ **Dimensional Inconsistency Alert:** " + " ".join(unit_notes)
            annotated_answer += unit_block

        # Stale or unverified material rates notice
        if rate_report.has_price_claims and not rate_report.is_reliable:
            rate_block = cls.get_stale_rate_note(language)
            if rate_block not in annotated_answer:
                annotated_answer += "\n\n" + rate_block

        # Regulatory interpretation warning if compliance asserted without official certification
        if reg_status == RegulatoryStatus.INTERPRETATION_UNVERIFIED:
            reg_warn = cls.get_unverified_regulation_note(language)
            if reg_warn not in annotated_answer:
                annotated_answer += "\n\n" + reg_warn

        return GroundedResponseEvaluation(
            evidence_status=ev_status,
            calculation_status=calc_status,
            regulatory_status=reg_status,
            citation_status=cit_status,
            tier=tier,
            is_grounded=is_grounded,
            citation_report=citation_report,
            calculation_audits=calc_audits,
            ungrounded_claims=ungrounded,
            unit_issues=unit_issues,
            rate_report=rate_report,
            regulatory_discrepancies=unverified_reg_clauses,
            disclosure_note=disclosure_note,
            annotated_answer=annotated_answer,
        )

    # ------------------------------------------------------------------------
    # LOCALIZED NATURAL DISCLOSURE NOTICES
    # ------------------------------------------------------------------------

    @staticmethod
    def get_unsupported_evidence_note(lang: str = "en") -> str:
        """Returns disclosure note when specific factual claims lack documentary grounding."""
        if lang == "roman_ur":
            return (
                "*[Dastavezi Hidayat: Is claim ko available documents se confirm nahi kiya ja saka. "
                "Barahe karam certified drawings aur site records se tasdeeq karein.]*"
            )
        elif lang == "ur":
            return (
                "*[دستاویزی رہنمائی: اس دعوے کی دستیاب دستاویزات سے تصدیق نہیں کی جا سکی۔ "
                "براہِ کرم مصدقہ ڈرائنگز اور سائیٹ ریکارڈ سے تصدیق کریں۔]*"
            )
        return (
            "*[Documentary Note: This factual or technical claim could not be confirmed against available project documents or codified records. "
            "Please verify against certified drawings.]*"
        )

    @staticmethod
    def get_unverified_calculation_note(lang: str = "en") -> str:
        """Returns notice when calculation cannot be reliably verified due to missing or ambiguous parameters."""
        if lang == "roman_ur":
            return (
                "*[Hisab Ki Hidayat: Di gayi information se calculation ko reliably verify karna mumkin nahi. "
                "Mukammal dimensions aur standard units faraham karein.]*"
            )
        elif lang == "ur":
            return (
                "*[حساب کا انتباہ: دی گئی معلومات سے حساب کو قابل اعتماد طریقے سے جانچنا ممکن نہیں ہے۔ "
                "براہ کرم مکمل پیمائش اور معیاری یونٹس فراہم کریں۔]*"
            )
        return (
            "*[Calculation Note: Calculation cannot be reliably verified from the provided information due to missing or ambiguous dimensions/units. "
            "Please provide complete dimensions and standard units.]*"
        )

    @staticmethod
    def get_unverified_regulation_note(lang: str = "en") -> str:
        """Returns disclosure when regulatory clause reference or legal interpretation cannot be verified."""
        if lang == "roman_ur":
            return (
                "*[Qawaneen Ki Hidayat: Is building-code clause ki official reference abhi verify nahi hui. "
                "Formal legal submission se pehle mutaliqa authority ke gazette se tasdeeq zaroor karein.]*"
            )
        elif lang == "ur":
            return (
                "*[قانونی انتباہ: بلڈنگ کوڈ کی اس شق کے سرکاری حوالے کی فی الوقت تصدیق نہیں ہوئی۔ "
                "باضابطہ جمع کرانے سے قبل متعلقہ ادارے کے گزٹ سے تصدیق لازمی ہے۔]*"
            )
        return (
            "*[Regulatory Note: Specific building-code clause or legal interpretation has not been verified against official codified records. "
            "Automated matching does not constitute legal or statutory compliance.]*"
        )

    @staticmethod
    def get_regulatory_unverified_note(lang: str = "en") -> str:
        """Returns disclosure note when cited or requested regulatory clauses lack documentary grounding."""
        if lang == "roman_ur":
            return (
                "*[Qawaneen Ki Hidayat: Upar diye gaye building byelaws ke clauses dastiyab verified documents se confirm nahi ho sake. "
                "Qanooni approval se pehle mutaliqa authority (LDA / CDA / SBCA / PBC) ke official gazette se tasdeeq zaroor karein.]*"
            )
        elif lang == "ur":
            return (
                "*[تکنیکی انتباہ: اوپر بیان کی گئی مخصوص ضوابط کی دفعات دستیاب تصدیق شدہ دستاویزات سے تصدیق نہیں ہو سکیں۔ "
                "حتمی قانونی منظوری سے قبل متعلقہ بلڈنگ کنٹرول اتھارٹی کے سرکاری گزٹ سے تصدیق لازمی ہے۔]*"
            )
        return (
            "*[Regulatory Note: Specific building byelaw clauses referenced above could not be verified against the authorized codified documents in the knowledgebase. "
            "Please consult the official gazetted regulations (LDA / CDA / SBCA / PBC) before submitting drawings for approval.]*"
        )

    @staticmethod
    def get_insufficient_evidence_note(lang: str = "en") -> str:
        """Returns disclosure note when documentary evidence is unavailable for specialized queries."""
        if lang == "roman_ur":
            return (
                "*[Dastavezi Hidayat: Is sawal ke liye makhsoos project documents ya codified byelaws dastiyab nahi hain. "
                "Yeh maloomat aam civil engineering usoolon par mabni hai.]*"
            )
        elif lang == "ur":
            return (
                "*[دستاویزی نوٹ: اس سوال سے متعلق مخصوص دستاویزات یا ضوابط فی الوقت دستیاب نہیں ہیں۔ "
                "اوپر دی گئی رہنمائی عمومی سول انجینئرنگ کے اصولوں پر مبنی ہے۔]*"
            )
        return (
            "*[Documentary Note: Detailed project-specific documents or official byelaw text are currently unavailable for this specific query. "
            "The explanation above is based on general civil engineering principles.]*"
        )

    @staticmethod
    def get_calculation_verified_note(lang: str = "en") -> str:
        """Returns confirmation note when engineering calculation has been checked by deterministic formula."""
        if lang == "roman_ur":
            return (
                "*[Hisab Ki Tasdeeq: Saria ka wazan (D^2/162) aur concrete ke hisab ki fanni formulas ke mutabiq tasdeeq kar li gayi hai.]*"
            )
        elif lang == "ur":
            return (
                "*[حساب کی تصدیق: سریے کے وزن اور کنکریٹ کی پیمائش کی تکنیکی فارمولوں کے مطابق تصدیق کی گئی ہے۔]*"
            )
        return (
            "*[Calculation Verified: Numerical quantities and formulas (e.g. D^2/162 for steel rebar, volumetric mix proportions) have been independently verified using deterministic engineering checks.]*"
        )

    @staticmethod
    def get_partially_supported_note(lang: str = "en") -> str:
        """Returns transparent note when answer is partially supported by evidence."""
        if lang == "roman_ur":
            return (
                "*[Tafseelat: Kuch hissay dastiyab documents se supported hain jabkay mazeed tafseelat site condition aur structural drawing par munhasir hain.]*"
            )
        elif lang == "ur":
            return (
                "*[تفصیلات: کچھ معلومات دستیاب دستاویزات سے تصدیق شدہ ہیں جبکہ باقی تفصیلات سائیٹ کی صورتحال اور سٹرکچرل ڈرائنگ پر منحصر ہیں۔]*"
            )
        return (
            "*[Partially Supported: Portions of this answer are supported by retrieved documents, while site-specific details require verification against certified project drawings.]*"
        )

    @staticmethod
    def get_calculation_verified_no_evidence_note(lang: str = "en") -> str:
        """Returns disclosure when calculation is verified but project documentary evidence is absent."""
        if lang == "roman_ur":
            return (
                "*[Hisab Ki Tasdeeq: Calculation verify ho gayi hai, lekin is result ko support karne ke liye project-specific document evidence available nahi hai.]*"
            )
        elif lang == "ur":
            return (
                "*[حساب کی تصدیق: حساب کی تصدیق ہو چکی ہے، لیکن اس نتیجے کی تائید کے لیے پراجیکٹ کے مخصوص دستاویزی شواہد دستیاب نہیں ہیں۔]*"
            )
        return (
            "*[Calculation Note: Calculation independently verified using deterministic engineering checks, but project-specific documentary evidence is unavailable for this result.]*"
        )

    @staticmethod
    def get_regulatory_reference_no_compliance_note(lang: str = "en") -> str:
        """Returns disclosure when regulatory reference exists but does not constitute statutory approval."""
        if lang == "roman_ur":
            return (
                "*[Qawaneen Ki Hidayat: Available regulatory reference verify ho gaya hai, lekin is se building ki complete legal compliance certify nahi hoti.]*"
            )
        elif lang == "ur":
            return (
                "*[قانونی رہنمائی: دستیاب ضابطے کے حوالے کی تصدیق ہو چکی ہے، لیکن اس سے عمارت کی مکمل قانونی منظوری ثابت نہیں ہوتی۔]*"
            )
        return (
            "*[Regulatory Note: Reference verified against available official regulatory text, but this does not constitute statutory certification or drawing approval.]*"
        )

    @staticmethod
    def get_missing_dimension_note(missing_dim: str = "thickness", lang: str = "en") -> str:
        """Returns notice when specific dimension is required to complete calculation."""
        if lang == "roman_ur":
            return (
                f"*[Hisab Ki Hidayat: Is calculation ke liye slab ki {missing_dim} required hai. Barah-e-karam {missing_dim} provide karein.]*"
            )
        elif lang == "ur":
            return (
                f"*[حساب کی رہنمائی: اس حساب کے لیے سلیب کی {missing_dim} درکار ہے۔ براہ کرم {missing_dim} فراہم کریں۔]*"
            )
        return (
            f"*[Calculation Note: For this calculation, {missing_dim} is required. Please provide the {missing_dim} dimension.]*"
        )

    @staticmethod
    def get_stale_rate_note(lang: str = "en") -> str:
        """Returns warning note when material prices are estimates or from older surveys."""
        if lang == "roman_ur":
            return (
                "*[Market Rate Note: Construction material rates (cement, steel) market mein taizi se tabdeel hotay hain. "
                "Yeh rates andaza hain, khareedari se qabal local market ya dealer se taza tareen qeemat zaroor maloom karein.]*"
            )
        elif lang == "ur":
            return (
                "*[مارکیٹ ریٹ نوٹ: تعمیراتی مٹیریل (سیمنٹ، سریا) کے نرخ مارکیٹ میں تیزی سے تبدیل ہوتے ہیں۔ "
                "خریداری سے قبل مقامی مارکیٹ سے تازہ ترین قیمت معلوم کریں۔]*"
            )
        return (
            "*[Market Rate Note: Construction commodity rates (cement, steel) fluctuate frequently with market volatility. "
            "These figures are general survey estimates; obtain real-time dealer quotations before procurement.]*"
        )
