"""
TameerAI - Construction Technical Accuracy & Engineering Formula Engine (Phase 03G Stage B3.1)

Provides deterministic verification of:
1. Standard civil engineering formulas (Rebar D^2/162, Concrete volume L*W*T, Nominal 1:2:4 cement bags 0.176*V, BOQ arithmetic Qty*Rate).
2. Dimensional and unit consistency (prevents equating volume with area or pressure with length).
3. Ungrounded high-impact construction claims (flags fabricated member sizing, unverified foundation depths).
4. Material rate reliability (detects missing sources, stale survey dates, and currency/unit mismatches).
"""

import math
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.ai.contracts.validation import CalculationStatus


# =====================================================================
# DATA CONTRACTS FOR TECHNICAL ACCURACY
# =====================================================================

class AccuracyIssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TechnicalAuditItem(BaseModel):
    """Detailed audit finding for a mathematical, dimensional, or technical assertion."""
    category: str  # formula, unit, ungrounded_claim, material_rate
    assertion_text: str
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    is_valid: bool
    calculation_status: Optional[CalculationStatus] = None
    severity: AccuracyIssueSeverity = AccuracyIssueSeverity.WARNING
    assumptions: Optional[str] = None
    input_units: Optional[str] = None
    explanation: str


class MaterialRateAuditReport(BaseModel):
    """Evaluation of commercial material price claims in AI outputs."""
    has_price_claims: bool = False
    is_reliable: bool = True
    stale_rates_detected: List[str] = Field(default_factory=list)
    missing_sources: List[str] = Field(default_factory=list)
    unverified_estimates: List[str] = Field(default_factory=list)
    details: List[TechnicalAuditItem] = Field(default_factory=list)


# =====================================================================
# 1. DETERMINISTIC ENGINEERING FORMULA VERIFIER
# =====================================================================

class EngineeringFormulaVerifier:
    """
    Deterministic validator for standard civil engineering equations used in Pakistan.
    Uses Decimal arithmetic and explicit tolerances.
    Supported formulas strictly limited to:
    1. Steel rebar weight: W = D^2 / 162.0 kg/m
    2. Concrete volume: V = L * W * T
    3. Nominal 1:2:4 concrete cement bag estimate: 0.176 * V
    4. BOQ arithmetic: Total = Quantity * Unit Rate
    """

    NOMINAL_124_ASSUMPTIONS: str = (
        "Nominal 1:2:4 Concrete Mix Assumptions: "
        "(1) Dry volume factor = 1.54 to account for interstitial aggregate void fill; "
        "(2) Proportions sum = 1 (cement) + 2 (sand) + 4 (coarse aggregate) = 7; "
        "(3) Volume of dry cement = (1 / 7) * 1.54 * V = 0.22 * V cft; "
        "(4) Standard commercial cement bag (50kg) bulk volume = 1.25 cft (bulk density ~1440 kg/m^3); "
        "(5) Bags required = (0.22 * V) / 1.25 = 0.176 * V (where V is wet concrete volume in cft). "
        "Intended strictly as a site volumetric rule-of-thumb for non-critical concrete. "
        "It is NOT a substitute for codified structural mix design (ACI 211 / BS 5328), water-cement ratio control, or cylinder compressive testing."
    )

    @staticmethod
    def calculate_steel_rebar_weight_kg_m(diameter_mm: float) -> float:
        """
        Calculates theoretical unit weight of deformed steel rebar in kg per linear meter.
        Formula: Weight = D^2 / 162.0 (derived from density of mild steel: 7850 kg/m^3).
        """
        if diameter_mm <= 0:
            return 0.0
        try:
            d_dec = Decimal(str(diameter_mm))
            w_dec = (d_dec * d_dec) / Decimal("162.0")
            return float(w_dec)
        except (InvalidOperation, ZeroDivisionError):
            return 0.0

    @classmethod
    def verify_rebar_weight(
        cls,
        diameter_mm: float,
        claimed_kg_m: float,
        tolerance_pct: float = 0.05,
    ) -> Tuple[bool, float, str]:
        """
        Verifies if an asserted rebar weight matches the standard D^2/162 formula within tolerance.
        Returns 3-tuple (is_valid, expected, explanation) for backward compatibility.
        """
        if diameter_mm <= 0 or claimed_kg_m <= 0:
            return False, 0.0, "Invalid diameter or claimed weight (must be > 0)."

        try:
            d_dec = Decimal(str(diameter_mm))
            c_dec = Decimal(str(claimed_kg_m))
            expected_dec = (d_dec * d_dec) / Decimal("162.0")
            expected = float(expected_dec)

            diff = abs(c_dec - expected_dec)
            pct_diff = float(diff / expected_dec)
            is_valid = round(pct_diff, 6) <= tolerance_pct
            diff_str = f"{pct_diff * 100.0:.1f}%"

            if is_valid:
                return True, expected, f"Verified: {claimed_kg_m:.3f} kg/m is consistent with standard D^2/162 ({expected:.3f} kg/m)."
            return False, expected, f"Calculation mismatch: For {diameter_mm}mm rebar, standard weight is ~{expected:.3f} kg/m (D^2/162), but {claimed_kg_m:.3f} kg/m was asserted (difference: {diff_str})."
        except (InvalidOperation, ZeroDivisionError):
            return False, 0.0, "Calculation error occurred during Decimal evaluation."

    @classmethod
    def verify_concrete_volume(
        cls,
        length_ft: float,
        width_ft: float,
        thickness_ft: float,
        claimed_volume_cft: float,
        tolerance_pct: float = 0.03,
    ) -> Tuple[bool, float, str]:
        """
        Verifies rectangular slab/footing volume calculation: V = L * W * T.
        All input dimensions must be strictly positive and in consistent feet units.
        """
        if length_ft <= 0 or width_ft <= 0 or thickness_ft <= 0:
            return False, 0.0, "Missing or non-positive dimension (Length, Width, and Thickness must all be > 0)."

        try:
            l_dec = Decimal(str(length_ft))
            w_dec = Decimal(str(width_ft))
            t_dec = Decimal(str(thickness_ft))
            c_dec = Decimal(str(claimed_volume_cft))

            expected_dec = l_dec * w_dec * t_dec
            expected = float(expected_dec)

            if expected <= 0:
                return False, 0.0, "Expected volume must be greater than zero."

            pct_diff = float(abs(c_dec - expected_dec) / expected_dec)
            is_valid = round(pct_diff, 6) <= tolerance_pct
            if is_valid:
                return True, expected, f"Verified: {claimed_volume_cft:.1f} cft matches L*W*T ({expected:.1f} cft)."
            return False, expected, f"Volume mismatch: {length_ft}ft x {width_ft}ft x {thickness_ft}ft = {expected:.1f} cft, but {claimed_volume_cft:.1f} cft was asserted."
        except (InvalidOperation, ZeroDivisionError):
            return False, 0.0, "Decimal evaluation error for concrete volume."

    @classmethod
    def verify_cement_bags_nominal_124(
        cls,
        volume_cft: float,
        claimed_bags: float,
        tolerance_pct: float = 0.10,
    ) -> Tuple[bool, float, str]:
        """
        Verifies nominal 1:2:4 volumetric batching cement requirement: Bags = 0.176 * V.
        """
        if volume_cft <= 0 or claimed_bags <= 0:
            return False, 0.0, "Invalid volume or claimed bag count (must be > 0)."

        try:
            v_dec = Decimal(str(volume_cft))
            c_dec = Decimal(str(claimed_bags))
            expected_dec = Decimal("0.176") * v_dec
            expected = float(expected_dec)

            pct_diff = float(abs(c_dec - expected_dec) / expected_dec)
            is_valid = round(pct_diff, 6) <= tolerance_pct
            if is_valid:
                return True, expected, f"Verified: {claimed_bags:.1f} bags is consistent with 1:2:4 nominal mix rule ({expected:.1f} bags for {volume_cft:.1f} cft)."
            return False, expected, f"Cement bag mismatch: For {volume_cft:.1f} cft of 1:2:4 concrete, expected ~{expected:.1f} bags (using dry multiplier 1.54), but {claimed_bags:.1f} bags was asserted."
        except (InvalidOperation, ZeroDivisionError):
            return False, 0.0, "Decimal evaluation error for cement bags."

    @classmethod
    def verify_boq_arithmetic(
        cls,
        quantity: float,
        unit_rate: float,
        claimed_total: float,
        tolerance_pct: float = 0.01,
    ) -> Tuple[bool, float, str]:
        """
        Verifies line item total = quantity * unit_rate using Decimal precision.
        """
        if quantity < 0 or unit_rate < 0 or claimed_total < 0:
            return False, 0.0, "Quantity, unit rate, and total must be non-negative."

        try:
            q_dec = Decimal(str(quantity))
            r_dec = Decimal(str(unit_rate))
            c_dec = Decimal(str(claimed_total))
            expected_dec = q_dec * r_dec
            expected = float(expected_dec)

            pct_diff = float(abs(c_dec - expected_dec) / expected_dec) if expected_dec != Decimal("0") else 0.0
            is_valid = round(pct_diff, 6) <= tolerance_pct
            if is_valid:
                return True, expected, f"Verified: {quantity} x {unit_rate} = {claimed_total}."
            return False, expected, f"Arithmetic mismatch: {quantity} x {unit_rate} = {expected:.2f}, but {claimed_total:.2f} was asserted."
        except (InvalidOperation, ZeroDivisionError):
            return False, 0.0, "Decimal evaluation error for BOQ arithmetic."

    @classmethod
    def audit_response_calculations(cls, text: str) -> List[TechnicalAuditItem]:
        """
        Parses text for explicit mathematical assertions and audits their engineering validity.
        Identifies unambiguous formulas vs unparseable/ambiguous inputs (returning NOT_VERIFIABLE).
        """
        items: List[TechnicalAuditItem] = []

        # 1. Audit Rebar Weight Assertions: e.g. "12mm ... 0.89 kg/m" or "16mm saria ... 1.58 kg"
        rebar_pattern = re.compile(
            r"\b(?P<dia>6|8|10|12|16|20|25|32)\s*(?P<unit>mm|m\.m\.)\b.*?\b(?:weight|wazan|is|equals?|approx|hoga|hota\s+hai)?\s*(?P<wt>\d+(?:\.\d+)?)\s*(?:kg(?:/m|\s*per\s*meter)?)\b",
            re.IGNORECASE,
        )
        for m in rebar_pattern.finditer(text):
            try:
                dia = float(m.group("dia"))
                wt = float(m.group("wt"))
                is_valid, exp, expl = cls.verify_rebar_weight(dia, wt)
                items.append(
                    TechnicalAuditItem(
                        category="formula",
                        assertion_text=m.group(0),
                        expected_value=f"{exp:.3f} kg/m",
                        observed_value=f"{wt:.3f} kg/m",
                        is_valid=is_valid,
                        calculation_status=CalculationStatus.VERIFIED if is_valid else CalculationStatus.MISMATCH,
                        severity=AccuracyIssueSeverity.INFO if is_valid else AccuracyIssueSeverity.WARNING,
                        assumptions="W = D^2 / 162.0 kg/m (mild steel density 7850 kg/m^3, nominal metric diameter)",
                        input_units="mm (diameter) -> kg/m (unit weight)",
                        explanation=expl,
                    )
                )
            except (ValueError, ZeroDivisionError):
                pass

        # Detect ambiguous / unverified rebar parsing (e.g. diameter without mm unit)
        ambiguous_rebar = re.compile(
            r"\b(?:saria|rebar)\s+(?P<num>\d+)\b(?!\s*mm)(?:.*?\b(?:weight|wazan)\s*(?:is|=)?\s*(?P<wt>\d+(?:\.\d+)?))",
            re.IGNORECASE,
        )
        for m in ambiguous_rebar.finditer(text):
            items.append(
                TechnicalAuditItem(
                    category="formula",
                    assertion_text=m.group(0),
                    is_valid=False,
                    calculation_status=CalculationStatus.NOT_VERIFIABLE,
                    severity=AccuracyIssueSeverity.WARNING,
                    input_units="ambiguous / missing unit",
                    explanation="Missing explicit metric unit ('mm') for rebar diameter; cannot verify weight deterministically without unambiguous unit specification.",
                )
            )

        # 2. Audit Concrete Volume: e.g. "10ft x 10ft x 0.5ft ... 50 cft" or "10 x 20 x 0.5 = 100 cft"
        volume_pattern = re.compile(
            r"\b(?P<l>\d+(?:\.\d+)?)\s*(?:ft|feet)?\s*(?:x|by|\*)\s*(?P<w>\d+(?:\.\d+)?)\s*(?:ft|feet)?\s*(?:x|by|\*)\s*(?P<t>\d+(?:\.\d+)?)\s*(?:ft|feet|in|inches)?\b.*?\b(?:volume|concrete)?\s*(?:is|=|hoga)?\s*(?P<vol>\d+(?:\.\d+)?)\s*(?:cft|cubic\s*feet)\b",
            re.IGNORECASE,
        )
        for m in volume_pattern.finditer(text):
            try:
                l_val = float(m.group("l"))
                w_val = float(m.group("w"))
                t_val = float(m.group("t"))
                vol_val = float(m.group("vol"))

                is_valid, exp, expl = cls.verify_concrete_volume(l_val, w_val, t_val, vol_val)
                items.append(
                    TechnicalAuditItem(
                        category="formula",
                        assertion_text=m.group(0),
                        expected_value=f"{exp:.1f} cft",
                        observed_value=f"{vol_val:.1f} cft",
                        is_valid=is_valid,
                        calculation_status=CalculationStatus.VERIFIED if is_valid else CalculationStatus.MISMATCH,
                        severity=AccuracyIssueSeverity.INFO if is_valid else AccuracyIssueSeverity.WARNING,
                        assumptions="Rectangular prism V = L * W * T",
                        input_units="feet (L, W, T) -> cubic feet (cft)",
                        explanation=expl,
                    )
                )
            except (ValueError, ZeroDivisionError):
                pass

        # Detect 2-dimension missing thickness claims (e.g. "10x20 slab volume is 200 cft")
        missing_dim_pattern = re.compile(
            r"\b(?P<dim1>\d+(?:\.\d+)?)\s*(?:x|by)\s*(?P<dim2>\d+(?:\.\d+)?)\s*(?:slab|footing|concrete)\b.*?\bvolume\s*(?:is|=|hoga)?\s*(?P<vol>\d+(?:\.\d+)?)\s*(?:cft|cubic\s*feet)\b",
            re.IGNORECASE,
        )
        for m in missing_dim_pattern.finditer(text):
            # If not already matched by 3-dimension pattern
            if " x " in m.group(0) and m.group(0).count(" x ") < 2 and "by" not in m.group(0) or m.group(0).count("by") < 2:
                items.append(
                    TechnicalAuditItem(
                        category="formula",
                        assertion_text=m.group(0),
                        is_valid=False,
                        calculation_status=CalculationStatus.NOT_VERIFIABLE,
                        severity=AccuracyIssueSeverity.WARNING,
                        explanation="Missing thickness/depth dimension; concrete volume requires Length, Width, and Thickness (L*W*T). Cannot verify 2D input for 3D volume.",
                    )
                )

        # 3. Audit Nominal 1:2:4 Cement Bags: e.g. "50 cft of 1:2:4 concrete requires 8.8 bags"
        nominal_pattern = re.compile(
            r"\b(?P<vol>\d+(?:\.\d+)?)\s*(?:cft|cubic\s*feet)\b.*?\b1:2:4\b.*?\b(?P<bags>\d+(?:\.\d+)?)\s*(?:bags|borian)\b",
            re.IGNORECASE,
        )
        for m in nominal_pattern.finditer(text):
            try:
                vol = float(m.group("vol"))
                bags = float(m.group("bags"))
                is_valid, exp, expl = cls.verify_cement_bags_nominal_124(vol, bags)
                items.append(
                    TechnicalAuditItem(
                        category="formula",
                        assertion_text=m.group(0),
                        expected_value=f"{exp:.1f} bags",
                        observed_value=f"{bags:.1f} bags",
                        is_valid=is_valid,
                        calculation_status=CalculationStatus.VERIFIED if is_valid else CalculationStatus.MISMATCH,
                        severity=AccuracyIssueSeverity.INFO if is_valid else AccuracyIssueSeverity.WARNING,
                        assumptions=cls.NOMINAL_124_ASSUMPTIONS,
                        input_units="cft (wet volume) -> 50kg cement bags",
                        explanation=expl,
                    )
                )
            except (ValueError, ZeroDivisionError):
                pass

        # 4. Audit BOQ Multiplication: e.g. "100 bags @ 1400 = 140,000" or "50 x 200 = 10000"
        boq_mult_pattern = re.compile(
            r"\b(?P<qty>\d+(?:\.\d+)?)\s*(?:bags|tons|sqft|cft|kg|units)?\s*(?:@|x|\*)\s*(?:pkr\s*|rs\.?\s*)?(?P<rate>\d+(?:\.\d+)?)\s*(?:=|\bequals?\b|\btotal\b|\bhota\s+hai\b)\s*(?:pkr\s*|rs\.?\s*)?(?P<tot>\d+(?:\.\d+)?)\b",
            re.IGNORECASE,
        )
        for m in boq_mult_pattern.finditer(text):
            try:
                qty = float(m.group("qty"))
                rate = float(m.group("rate"))
                tot = float(m.group("tot"))
                is_valid, exp, expl = cls.verify_boq_arithmetic(qty, rate, tot)
                items.append(
                    TechnicalAuditItem(
                        category="formula",
                        assertion_text=m.group(0),
                        expected_value=f"{exp:.2f}",
                        observed_value=f"{tot:.2f}",
                        is_valid=is_valid,
                        calculation_status=CalculationStatus.VERIFIED if is_valid else CalculationStatus.MISMATCH,
                        severity=AccuracyIssueSeverity.INFO if is_valid else AccuracyIssueSeverity.WARNING,
                        assumptions="BOQ line item: Total = Quantity * Unit Rate",
                        explanation=expl,
                    )
                )
            except (ValueError, ZeroDivisionError):
                pass

        return items


# =====================================================================
# 2. UNIT & DIMENSIONAL CONSISTENCY AUDITOR
# =====================================================================

class UnitConsistencyAuditor:
    """
    Detects physically incompatible dimensional assertions in construction answers.
    e.g., asserting volume in square feet, pressure/strength in cubic feet, or mixing incompatible systems.
    """

    INCOMPATIBLE_DIMENSION_PATTERNS = [
        # Volume asserted with area units
        (re.compile(r"\b(?:volume|concrete\s+quantity)\b.*?\b\d+(?:\.\d+)?\s*(?:sqft|square\s+feet|sq\s+m|marla|kanal)\b", re.IGNORECASE),
         "Volume or concrete quantity cannot be measured in area units (sqft / square meters). Expected cft or cu.m."),
        
        # Slab thickness asserted with area units
        (re.compile(r"\b(?:thickness|depth)\b.*?\b\d+(?:\.\d+)?\s*(?:sqft|sq\s+inches|marla)\b", re.IGNORECASE),
         "Thickness or depth cannot be measured in area units. Expected inches, mm, or feet."),

        # Concrete strength / pressure asserted with volume or length units
        (re.compile(r"\b(?:strength|compressive\s+strength|bearing\s+capacity)\b.*?\b\d+(?:\.\d+)?\s*(?:cft|cu\s+m|feet|inches|mm)\b", re.IGNORECASE),
         "Strength or bearing capacity cannot be measured in volume or length units. Expected psi, MPa, or tons/sqft."),

        # Area asserted with volume units
        (re.compile(r"\b(?:plot\s+area|covered\s+area|floor\s+area)\b.*?\b\d+(?:\.\d+)?\s*(?:cft|cubic\s+feet|cu\s+m)\b", re.IGNORECASE),
         "Floor or plot area cannot be measured in cubic units. Expected sqft, marla, or kanal."),
    ]

    @classmethod
    def audit_unit_consistency(cls, text: str) -> List[TechnicalAuditItem]:
        """Audits text for dimensional mismatches and physical unit errors."""
        items: List[TechnicalAuditItem] = []
        for pat, reason in cls.INCOMPATIBLE_DIMENSION_PATTERNS:
            for m in pat.finditer(text):
                items.append(
                    TechnicalAuditItem(
                        category="unit",
                        assertion_text=m.group(0),
                        is_valid=False,
                        calculation_status=CalculationStatus.NOT_VERIFIABLE,
                        severity=AccuracyIssueSeverity.CRITICAL,
                        explanation=reason,
                    )
                )
        return items


# =====================================================================
# 3. UNGROUNDED HIGH-IMPACT CLAIM DETECTOR
# =====================================================================

class UngroundedClaimDetector:
    """
    Identifies high-impact construction claims that mandate documented site data
    or calculation proof, flagging them if presented without supporting evidence.
    """

    UNGROUNDED_SIZING_PATTERNS = [
        # Prescribing exact column rebar schedules without site calculations
        (re.compile(r"\b(?:use|provide|dalain|add)\s+(?:\d+)\s*(?:bars|saria|rebars?|nos?\.?)\s*(?:of\s+)?(?:\d+\s*mm|#\d|sooter)\s*(?:for\s+(?:your\s+)?(?:column|pillar|main\s+beam))\b", re.IGNORECASE),
         "Fabricated structural member reinforcement schedule asserted without site structural engineering calculations."),

        # Prescribing specific foundation depth without soil bearing capacity report
        (re.compile(r"\b(?:foundation|footing|bunyaad)\s*(?:depth\s+)?(?:must\s+be|should\s+be|rakhein|honi\s+chahiye)\s*(?:strictly\s+)?(?:\d+(?:\.\d+)?)\s*(?:feet|ft|meter|m)\b", re.IGNORECASE),
         "Definitive foundation depth asserted without geotechnical borehole investigation or soil bearing capacity data."),

        # Sizing column dimensions for multi-storey buildings without calculations
        (re.compile(r"\b(?:\d+\s+by\s+\d+|\d+\s*x\s*\d+)\s*(?:inch|inches)\s*(?:column\s+is\s+(?:sufficient|safe|enough))\s*(?:for\s+\d+\s+(?:floors?|storeys?))\b", re.IGNORECASE),
         "Asserted column physical cross-section sufficiency without structural axial load calculations."),

        # Uncalculated structural changes
        (re.compile(r"\b(?:add|remove|modify)\s+.*?\bwithout\s+(?:engineering\s+)?calculations\b", re.IGNORECASE),
         "Structural modifications recommended without engineering structural calculations."),

        # Absolute code compliance guarantees without verified documentation
        (re.compile(r"\b(?:this\s+design\s+is|it\s+is)\s*(?:100%|strictly|fully)\s*(?:compliant\s+with|approved\s+by)\s*(?:lda|cda|sbca|bcp)\b", re.IGNORECASE),
         "Absolute regulatory compliance asserted without verified codified byelaw document evidence."),
    ]

    @classmethod
    def detect_ungrounded_claims(
        cls,
        text: str,
        has_verified_evidence: bool = False,
        evidence_text: Optional[str] = None,
    ) -> List[TechnicalAuditItem]:
        """
        Detects ungrounded structural and regulatory sizing assertions when evidence is absent or does not support the specific claim.
        """
        items: List[TechnicalAuditItem] = []
        clean_evidence = (evidence_text or "").lower()

        for pat, expl in cls.UNGROUNDED_SIZING_PATTERNS:
            for m in pat.finditer(text):
                match_str = m.group(0).lower()
                # Flag if no verified evidence, or if the specific claim is not in evidence, or if explicitly uncalculated
                if not has_verified_evidence or (evidence_text and match_str not in clean_evidence) or "without calculations" in text.lower():
                    items.append(
                        TechnicalAuditItem(
                            category="ungrounded_claim",
                            assertion_text=m.group(0),
                            is_valid=False,
                            severity=AccuracyIssueSeverity.WARNING,
                            explanation=expl,
                        )
                    )
        return items


# =====================================================================
# 4. MATERIAL RATE RELIABILITY VERIFIER
# =====================================================================

class MaterialRateReliabilityVerifier:
    """
    Audits commercial material prices mentioned in AI text against verifiable
    market rate survey metadata, enforcing source presence, date freshness, and currency/unit integrity.
    """

    PRICE_ASSERTION_PATTERNS = [
        re.compile(r"\b(?P<mat>cement|saria|steel|bricks?|itain|sand|ret|bajri|crush)\b.*?\b(?:pkr|rs\.?)\s*(?P<price>\d+(?:,\d+)*(?:\.\d+)?)\s*(?P<unit>per\s+(?:bag|ton|1000|cft|sqft|kg))?\b", re.IGNORECASE),
        re.compile(r"\b(?:pkr|rs\.?)\s*(?P<price>\d+(?:,\d+)*(?:\.\d+)?)\s*(?P<unit>per\s+(?:bag|ton|1000|cft|sqft|kg))\s*(?:for\s+)?(?P<mat>cement|saria|steel|bricks?|itain|sand|ret|bajri|crush)\b", re.IGNORECASE),
    ]

    # Pattern detecting rate claims missing explicit currency or measurement unit
    MISSING_CURRENCY_OR_UNIT_PATTERN = re.compile(
        r"\b(?P<mat>cement|saria|steel|bricks?|itain)\s+(?:rate|price|qeemat|cost)?\s*(?:is|=|hoga|hai)?\s*(?P<val>\d{3,6})\b(?!\s*(?:pkr|rs|per|bag|ton|cft|sqft|kg))",
        re.IGNORECASE,
    )

    @classmethod
    def audit_material_rates(
        cls,
        text: str,
        available_rates: Optional[List[Any]] = None,
        max_freshness_days: int = 90,
    ) -> MaterialRateAuditReport:
        """
        Evaluates material prices mentioned in the response.
        Detects missing sources, stale survey dates, and currency/unit issues.
        """
        items: List[TechnicalAuditItem] = []
        stale_rates: List[str] = []
        missing_sources: List[str] = []
        unverified_estimates: List[str] = []
        has_prices = False

        # 1. Audit explicit price assertions with currency and unit
        rates_by_name: Dict[str, Any] = {}
        if available_rates:
            for r in available_rates:
                name_key = (getattr(r, "name", None) or getattr(r, "product_name", "")).lower()
                cat_key = getattr(r, "category", "").lower()
                if name_key:
                    rates_by_name[name_key] = r
                if cat_key:
                    rates_by_name[cat_key] = r

        for pat in cls.PRICE_ASSERTION_PATTERNS:
            for m in pat.finditer(text):
                has_prices = True
                mat = m.group("mat").lower()
                price_str = m.group("price").replace(",", "")
                unit_str = m.group("unit")
                assertion = m.group(0)

                # Check if unit is missing in the matched phrase
                if not unit_str:
                    items.append(
                        TechnicalAuditItem(
                            category="material_rate",
                            assertion_text=assertion,
                            is_valid=False,
                            severity=AccuracyIssueSeverity.WARNING,
                            explanation=f"Material rate for '{mat.title()}' lacks a clear unit of measurement (e.g. per bag, per ton, per cft).",
                        )
                    )

                matched_rate = None
                for k, r in rates_by_name.items():
                    if k in mat or mat in k:
                        matched_rate = r
                        break

                if matched_rate is None:
                    # Price asserted without any database survey record
                    unit_label = unit_str or "unspecified unit"
                    unverified_estimates.append(f"{mat.title()} (~PKR {price_str} {unit_label})")
                    missing_sources.append(mat.title())
                    items.append(
                        TechnicalAuditItem(
                            category="material_rate",
                            assertion_text=assertion,
                            is_valid=False,
                            severity=AccuracyIssueSeverity.WARNING,
                            explanation=f"Material price for '{mat.title()}' lacks a verified market survey record in the database. Must be clearly presented as an estimate.",
                        )
                    )
                else:
                    # Record found - check freshness and source
                    observed_at = (
                        getattr(matched_rate, "observed_at", None)
                        or getattr(matched_rate, "published_at", None)
                        or getattr(matched_rate, "collected_at", None)
                    )
                    source_name = getattr(matched_rate, "source_name", None)
                    status = getattr(matched_rate, "verification_status", "unverified")

                    is_stale = False
                    if observed_at:
                        now = datetime.now(timezone.utc)
                        if observed_at.tzinfo is None:
                            now = datetime.utcnow()
                        age_days = (now - observed_at).days
                        if age_days > max_freshness_days:
                            is_stale = True

                    if status == "stale" or is_stale:
                        stale_rates.append(f"{mat.title()} ({getattr(matched_rate, 'name', mat)})")
                        items.append(
                            TechnicalAuditItem(
                                category="material_rate",
                                assertion_text=assertion,
                                is_valid=False,
                                severity=AccuracyIssueSeverity.WARNING,
                                explanation=f"Material rate for '{mat.title()}' is based on historical survey data ({observed_at.strftime('%Y-%m-%d') if observed_at else 'unknown date'}) and may not reflect current volatile market rates.",
                            )
                        )
                    elif not source_name:
                        missing_sources.append(mat.title())
                        items.append(
                            TechnicalAuditItem(
                                category="material_rate",
                                assertion_text=assertion,
                                is_valid=False,
                                severity=AccuracyIssueSeverity.WARNING,
                                explanation=f"Material rate for '{mat.title()}' lacks an authoritative reporting agency source.",
                            )
                        )
                    else:
                        items.append(
                            TechnicalAuditItem(
                                category="material_rate",
                                assertion_text=assertion,
                                is_valid=True,
                                severity=AccuracyIssueSeverity.INFO,
                                explanation=f"Verified against {source_name} survey data ({observed_at.strftime('%Y-%m-%d') if observed_at else 'recent'}).",
                            )
                        )

        # 2. Check for naked rate assertions missing currency or unit
        for m in cls.MISSING_CURRENCY_OR_UNIT_PATTERN.finditer(text):
            has_prices = True
            mat = m.group("mat")
            val = m.group("val")
            items.append(
                TechnicalAuditItem(
                    category="material_rate",
                    assertion_text=m.group(0),
                    is_valid=False,
                    severity=AccuracyIssueSeverity.WARNING,
                    explanation=f"Material rate claim for '{mat}' ({val}) lacks explicit currency specification (PKR) or standard unit of measurement.",
                )
            )

        is_reliable = (len(stale_rates) == 0 and len(unverified_estimates) == 0 and not any(not i.is_valid for i in items))

        return MaterialRateAuditReport(
            has_price_claims=has_prices,
            is_reliable=is_reliable,
            stale_rates_detected=stale_rates,
            missing_sources=missing_sources,
            unverified_estimates=unverified_estimates,
            details=items,
        )
