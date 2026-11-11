"""
TameerAI - Document Chunking Rules & Clause Detection (Phase 03C)
Provides regex patterns and boundary analysis for Pakistani building codes,
planning regulations, and FIDIC engineering contracts.
"""

import re
from typing import List, Optional, Tuple

# Regex patterns for detecting chapters, sections, clauses, and engineering schedules
CHAPTER_PATTERN = re.compile(
    r"^(?:CHAPTER|Chapter)\s+([0-9IVXLCDM]+)[\s:\-–—]+(.*)$",
    re.MULTILINE
)

SECTION_PATTERN = re.compile(
    r"^(?:SECTION|Section|SEC\.)\s+([0-9]+(?:\.[0-9]+)*)[\s:\-–—]+(.*)$",
    re.MULTILINE
)

CLAUSE_PATTERN = re.compile(
    r"^(?:CLAUSE|Clause|Rule|RULE|Article|ARTICLE)\s+([0-9]+(?:\.[0-9]+)*(?:\([a-zA-Z0-9]+\))*)[\s:\-–—]+(.*)$",
    re.MULTILINE
)

# Inline reference pattern to avoid breaking across chunks
INLINE_REGULATORY_REF = re.compile(
    r"(?:(?:Section|Clause|Rule|Article|Table)\s+[0-9]+(?:\.[0-9]+)*(?:\([a-z0-9]+\))*)",
    re.IGNORECASE
)


def extract_headings(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the most prominent chapter and section/clause heading from a text block.
    Returns (chapter, section).
    """
    chapter = None
    section = None

    chap_match = CHAPTER_PATTERN.search(text)
    if chap_match:
        c_num, c_title = chap_match.groups()
        chapter = f"Chapter {c_num.strip()}: {c_title.strip()[:100]}"

    sec_match = SECTION_PATTERN.search(text)
    if sec_match:
        s_num, s_title = sec_match.groups()
        section = f"Section {s_num.strip()}: {s_title.strip()[:100]}"
    else:
        clause_match = CLAUSE_PATTERN.search(text)
        if clause_match:
            cl_num, cl_title = clause_match.groups()
            section = f"Clause {cl_num.strip()}: {cl_title.strip()[:100]}"

    return chapter, section


def split_into_semantic_paragraphs(text: str) -> List[str]:
    """
    Splits text into cohesive paragraphs and sections.
    Preserves clause boundaries and structural headings.
    """
    if not text:
        return []

    # Standardize line endings
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split on double linebreaks or on lines starting with Chapter/Section/Clause
    raw_paras = re.split(r"\n{2,}", normalized)
    paragraphs: List[str] = []

    for para in raw_paras:
        p_clean = para.strip()
        if not p_clean:
            continue

        # If a single paragraph is very long but contains multiple clauses, split at clause lines
        lines = p_clean.split("\n")
        current_block: List[str] = []

        for line in lines:
            line_str = line.strip()
            is_new_header = (
                CHAPTER_PATTERN.match(line_str)
                or SECTION_PATTERN.match(line_str)
                or CLAUSE_PATTERN.match(line_str)
            )

            if is_new_header and current_block:
                joined = "\n".join(current_block).strip()
                if joined:
                    paragraphs.append(joined)
                current_block = [line_str]
            else:
                current_block.append(line_str)

        if current_block:
            joined = "\n".join(current_block).strip()
            if joined:
                paragraphs.append(joined)

    return paragraphs

