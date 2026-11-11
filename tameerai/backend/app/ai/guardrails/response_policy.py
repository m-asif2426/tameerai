"""
TameerAI - Construction Natural Response Policy & Off-Topic Handler (Phase 03D)
Formats natural, context-aware responses in English, Urdu, and Roman Urdu.
Politely redirects off-topic questions without invoking expensive LLM or retrieval calls.
"""

import re
from typing import Any, Dict, List, Optional

# Roman Urdu common function words for language detection
ROMAN_URDU_WORDS = {
    "kya", "kia", "hai", "hain", "kaise", "kese", "kitna", "kitni", "kitne", "mein",
    "karna", "karo", "bhai", "hoga", "hogi", "hoti", "chahiye", "karun", "rahe",
    "batao", "walay", "wala", "wali", "rakhna", "lagti", "lagta", "aur", "hota",
}

# Urdu unicode script range
URDU_SCRIPT_PATTERN = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    """
    Detects whether user prompt is English ('en'), Urdu script ('ur'), or Roman Urdu ('roman_ur').
    """
    if not text:
        return "en"

    # Check for Urdu Nastaliq / Arabic unicode characters
    if URDU_SCRIPT_PATTERN.search(text):
        return "ur"

    tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    roman_urdu_matches = tokens.intersection(ROMAN_URDU_WORDS)

    # If two or more Roman Urdu markers are present, classify as Roman Urdu
    if len(roman_urdu_matches) >= 2 or (len(tokens) <= 5 and len(roman_urdu_matches) >= 1):
        return "roman_ur"

    return "en"


class ConstructionResponsePolicy:
    """
    Natural conversation policy enforcing language adaptation,
    unpretentious professional tone, and polite off-topic redirection.
    """

    @staticmethod
    def get_off_topic_redirect(lang: str = "en") -> str:
        """Returns a polite, localized off-topic redirection message."""
        if lang == "roman_ur":
            return (
                "Main TameerAI hoon aur sirf construction aur civil engineering topics mein madad karta hoon. "
                "Aap building design, materials, foundation, BOQ ya site work se mutaliq sawal pooch sakte hain."
            )
        elif lang == "ur":
            return (
                "میں تعمیر اے آئی ہوں اور صرف تعمیرات اور سول انجینئرنگ کے موضوعات پر رہنمائی فراہم کرتا ہوں۔ "
                "آپ عمارت کے ڈیزائن، مٹیریل، فاؤنڈیشن، تخمینہ لاگت یا سائیٹ کے کام سے متعلق سوالات پوچھ سکتے ہیں۔"
            )
        return (
            "I am TameerAI, dedicated exclusively to construction and civil engineering. "
            "Please ask questions related to architectural planning, structural design, building materials, "
            "cost estimation (BOQ), or construction regulations."
        )

    @staticmethod
    def get_ambiguous_clarification(lang: str = "en") -> str:
        """Returns a polite clarification request for ambiguous or underspecified queries."""
        if lang == "roman_ur":
            return (
                "Aap ka sawal mukhtasir ya ghair wazeh hai. Kiya aap building construction ya civil engineering ke context mein "
                "pooch rahe hain? Barah-e-karam thori mazeed tafseelat faraham karein."
            )
        elif lang == "ur":
            return (
                "آپ کا سوال غیر واضح ہے۔ کیا آپ عمارت کی تعمیر یا سول انجینئرنگ کے حوالے سے پوچھ رہے ہیں؟ "
                "براہ کرم تھوڑی مزید تفصیلات فراہم کریں۔"
            )
        return (
            "Your question is a bit ambiguous. Are you inquiring in the context of building construction, "
            "structural design, or civil works? Please provide a little more detail."
        )

    @classmethod
    def get_intelligent_clarification(
        cls,
        context: Optional[object] = None,
        lang: str = "en",
        query: str = "",
        is_mixed_inseparable: bool = False,
    ) -> str:
        """
        Generates context-aware, targeted engineering clarification.
        Avoids generic responses by directly requesting specific missing parameters.
        """
        # 1. Inseparable mixed topic case
        if is_mixed_inseparable:
            if lang == "roman_ur":
                return (
                    "Aap ke sawal mein construction aur ghair-mutaliqa topics shamil hain jinhein alag nahi kiya ja saka. "
                    "Barah-e-karam sirf civil engineering ya construction se mutaliq hissa wazeh karein taakay tafseelat di ja sakein."
                )
            elif lang == "ur":
                return (
                    "آپ کے سوال میں تعمیراتی اور غیر متعلقہ موضوعات دونوں شامل ہیں جنہیں الگ نہیں کیا جا سکا۔ "
                    "براہ کرم صرف سول انجینئرنگ یا تعمیراتی حصے کی تفصیلات فراہم کریں۔"
                )
            return (
                "Your question combines construction and unrelated topics that cannot be safely separated. "
                "Please clarify the specific civil engineering or construction question you would like addressed."
            )

        # 2. Context-derived specific missing variable clarifications
        if context:
            lower_q = query.lower()
            topic = getattr(context, "topic", "")
            missing_vars = [mv.name for mv in getattr(context, "missing_variables", [])]

            # Case: Foundation design or depth without structural loads/soil
            if "Foundation" in topic or any(w in lower_q for w in ["bunyaad", "foundation"]):
                if any(v in missing_vars for v in ["soil_bearing_capacity", "structural_load", "building_floors"]) or "design" in lower_q:
                    if lang == "roman_ur":
                        return (
                            "Foundation ka design samajhne ke liye building ki floors, soil bearing capacity aur approximate structural loads ki information chahiye. "
                            "Kya aap ye details share kar sakte hain?"
                        )
                    elif lang == "ur":
                        return (
                            "فاؤنڈیشن کے ڈیزائن کے لیے عمارت کی منزلیں، مٹی کی بیئرنگ کپیسٹی اور اندازاً ساختی بوجھ کی تفصیلات درکار ہوتی ہیں۔ "
                            "کیا آپ یہ معلومات فراہم کر سکتے ہیں؟"
                        )
                    return (
                        "To design or understand the foundation requirements, information on the building storeys (floors), soil bearing capacity, "
                        "and approximate structural loads is needed. Could you please share these details?"
                    )

            # Case: Concrete calculation without volume or mix specification
            if "Concrete" in topic or any(w in lower_q for w in ["concrete", "concreet"]):
                if any(w in lower_q for w in ["calculation", "calculate", "hisab", "quantity"]) or getattr(context, "is_calculation_required", False):
                    if lang == "roman_ur":
                        return (
                            "Aap concrete ki quantity calculate karna chahte hain ya concrete mix ratio? "
                            "Agar quantity chahiye to length, width aur thickness share karein."
                        )
                    elif lang == "ur":
                        return (
                            "کیا آپ کنکریٹ کی مقدار کا حساب لگانا چاہتے ہیں یا مکس ریشو؟ "
                            "اگر مقدار درکار ہے تو براہ کرم لمبائی، چوڑائی اور موٹائی فراہم کریں۔"
                        )
                    return (
                        "Are you looking to calculate concrete quantity (volume) or the concrete mix ratio? "
                        "If you need quantity calculation, please provide the length, width, and thickness."
                    )

            # Case: Rebar/steel calculation without diameter or length
            if any(w in lower_q for w in ["saria", "sariya", "rebar", "steel"]):
                if any(w in lower_q for w in ["weight", "wazan", "calculate", "hisab"]):
                    if lang == "roman_ur":
                        return (
                            "Saria (rebar) ka weight calculate karne ke liye diameter (maslan 4 sooter ya 12mm) aur total length share karein "
                            "taakay formula (D^2/162) ke mutabiq hisab lagaya ja sake."
                        )
                    elif lang == "ur":
                        return (
                            "سریہ کا وزن معلوم کرنے کے لیے قطر اور لمبائی کی تفصیلات فراہم کریں۔"
                        )
                    return (
                        "To calculate steel rebar weight, please specify the bar diameter (e.g., 12mm or #4 bar) and length so we can calculate it accurately."
                    )

            # Case: Explicit clarification prompt stored in context
            if getattr(context, "clarification_question", None):
                return context.clarification_question

        # 3. Fallback to general ambiguous clarification
        return cls.get_ambiguous_clarification(lang)

    @staticmethod
    def get_mixed_topic_prefix(lang: str = "en") -> str:
        """Prefix indicating that only the construction portion of a mixed query is being answered."""
        if lang == "roman_ur":
            return "[Note: Main sirf construction se mutaliq hissay ka jawab de raha hoon:]\n\n"
        elif lang == "ur":
            return "[نوٹ: میں صرف تعمیراتی حصے کا جواب فراہم کر رہا ہوں:]\n\n"
        return "[Note: Addressing only the construction-related portion of your question:]\n\n"

    @staticmethod
    def get_critical_safety_advisory(lang: str = "en") -> str:
        """Returns life-safety emergency directive for Level 4 CRITICAL hazards."""
        from app.ai.guardrails.structural_safety import StructuralSafetyEngine
        return StructuralSafetyEngine.get_critical_safety_advisory(lang=lang)

    @staticmethod
    def get_high_risk_structural_advisory(
        category: Optional[Any] = None,
        missing_vars: Optional[List[str]] = None,
        lang: str = "en",
    ) -> str:
        """Returns structural alteration and high-risk design advisory for Level 3 HIGH."""
        from app.ai.guardrails.structural_safety import HazardCategory, StructuralSafetyEngine
        cat = category or HazardCategory.STRUCTURAL_MODIFICATION
        m_vars = missing_vars or []
        return StructuralSafetyEngine.get_high_risk_advisory(category=cat, missing_vars=m_vars, lang=lang)

