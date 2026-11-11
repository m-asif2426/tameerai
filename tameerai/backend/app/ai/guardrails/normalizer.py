"""
TameerAI - Multilingual Construction Text Normalizer (Phase 03F)
Layer 1 of the Intelligent Construction Intent Architecture.
Handles normalization of lowercase/uppercase variations, whitespace, punctuation,
common spelling errors, Roman Urdu phonetic variations, mixed-language code switching,
and civil engineering abbreviations.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


# Common phonetic and typographical spelling variations mapped to canonical terms
ROMAN_URDU_SPELLING_MAP: Dict[str, str] = {
    # Foundation & Excavation
    "bunyad": "bunyaad",
    "buniyad": "bunyaad",
    "buniad": "bunyaad",
    "bunyadd": "bunyaad",
    "bunyaado": "bunyaad",
    "khudai": "khudai",
    "khudaee": "khudai",
    "khoodai": "khudai",
    "khodai": "khudai",
    "borma": "borehole",

    # Steel / Rebar
    "saria": "saria",
    "sariya": "saria",
    "saryia": "saria",
    "sarria": "saria",
    "loha": "steel",
    "rebar": "rebar",

    # Concrete & Ingredients
    "cemnt": "cement",
    "ciment": "cement",
    "cament": "cement",
    "simint": "cement",
    "concreet": "concrete",
    "concerete": "concrete",
    "concrite": "concrete",
    "bajri": "bajri",
    "bajree": "bajri",
    "bajari": "bajri",
    "ret": "ret",
    "rait": "ret",
    "rayt": "ret",
    "crush": "aggregate",

    # Execution & Site Work
    "shutraing": "shuttering",
    "shuttring": "shuttering",
    "shutring": "shuttering",
    "shaterang": "shuttering",
    "formwrk": "formwork",
    "tarai": "curing",
    "terai": "curing",
    "trai": "curing",
    "taree": "curing",
    "dhalai": "dhalai",
    "dhalaee": "dhalai",
    "dhlai": "dhalai",
    "plastar": "plaster",
    "palastar": "plaster",
    "plastring": "plastering",
    "darar": "crack",
    "daraar": "crack",
    "dararain": "cracks",
    "seep": "seepage",
    "seepg": "seepage",
    "shora": "efflorescence",
    "deemak": "termite",

    # Components
    "lanter": "lanter",
    "lenter": "lanter",
    "linteer": "lintel",
    "chhat": "roof_slab",
    "chat": "roof_slab",
    "chhatt": "roof_slab",
    "deewar": "wall",
    "dewar": "wall",
    "diwar": "wall",
    "farsh": "floor",
    "farash": "floor",
    "chokhat": "door_frame",
    "darwaza": "door",
    "khirki": "window",
    "khidki": "window",
    "tehkhaana": "basement",
    "tehkhana": "basement",

    # Materials
    "eent": "brick",
    "int": "brick",
    "eentein": "bricks",
    "bhatta": "brick_kiln",

    # Management & Stakeholders
    "thekedar": "thekedar",
    "thekaydar": "thekedar",
    "thekedaar": "thekedar",
    "mistri": "mistri",
    "mistry": "mistri",
    "mazdoor": "mazdoor",
    "majdoor": "mazdoor",
    "naksha": "naqsha",
    "naqsha": "naqsha",
}

# Technical engineering and land measurement abbreviations
CONSTRUCTION_ABBREVIATIONS: Dict[str, str] = {
    "rcc": "reinforced cement concrete",
    "pcc": "plain cement concrete",
    "dpc": "damp proof course",
    "boq": "bill of quantities",
    "spt": "standard penetration test",
    "mpa": "megapascal",
    "psi": "pounds per square inch",
    "sqft": "square feet",
    "sq.ft": "square feet",
    "sft": "square feet",
    "sqyd": "square yards",
    "sq.yd": "square yards",
    "cft": "cubic feet",
    "cbm": "cubic meters",
    "cum": "cubic meters",
    "lda": "lahore development authority",
    "cda": "capital development authority",
    "sbca": "sindh building control authority",
    "kda": "karachi development authority",
    "pec": "pakistan engineering council",
    "bcp": "building code of pakistan",
    "mep": "mechanical electrical plumbing",
    "far": "floor area ratio",
    "noc": "no objection certificate",
    "dia": "diameter",
    "c/c": "center to center",
}


class NormalizedQuery(BaseModel):
    """Encapsulates raw, cleaned, and canonically normalized tokens of a query."""
    raw_query: str
    cleaned_query: str
    normalized_query: str
    tokens: List[str]
    detected_abbreviations: Dict[str, str] = Field(default_factory=dict)
    normalized_terms: Dict[str, str] = Field(default_factory=dict)


class TextNormalizer:
    """
    High-performance, deterministic text normalizer for construction queries.
    Cleans punctuation, standardizes Roman Urdu spelling variations, and resolves abbreviations.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes duplicate whitespace, zero-width characters, non-standard control characters, and standardizes punctuation."""
        if not text:
            return ""
        # Strip zero-width spaces, joiners, and BOM
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        # Collapse multiple spaces, tabs, and newlines
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned

    @classmethod
    def normalize(cls, text: str) -> NormalizedQuery:
        """
        Executes full normalization pipeline on raw user query.
        """
        cleaned = cls.clean_text(text)
        lower_cleaned = cleaned.lower()

        # Tokenize preserving alphanumeric words, hyphenated units, and Unicode/Urdu script tokens
        raw_tokens = re.findall(r"[\w\-.:/]+", lower_cleaned)

        detected_abbrs: Dict[str, str] = {}
        normalized_terms_map: Dict[str, str] = {}
        transformed_tokens: List[str] = []

        for token in raw_tokens:
            # Check abbreviations
            if token in CONSTRUCTION_ABBREVIATIONS:
                expansion = CONSTRUCTION_ABBREVIATIONS[token]
                detected_abbrs[token] = expansion
                transformed_tokens.append(token)
                continue

            # Check Roman Urdu spelling variations
            if token in ROMAN_URDU_SPELLING_MAP:
                canonical = ROMAN_URDU_SPELLING_MAP[token]
                normalized_terms_map[token] = canonical
                transformed_tokens.append(token)
                continue

            transformed_tokens.append(token)

        # Build normalized representation string
        # Replace spelling variants in text safely
        normalized_str = lower_cleaned
        for var_token, canon in normalized_terms_map.items():
            pattern = r"\b" + re.escape(var_token) + r"\b"
            normalized_str = re.sub(pattern, canon, normalized_str)

        return NormalizedQuery(
            raw_query=text,
            cleaned_query=cleaned,
            normalized_query=normalized_str,
            tokens=transformed_tokens,
            detected_abbreviations=detected_abbrs,
            normalized_terms=normalized_terms_map,
        )

