import sys
from pathlib import Path
import re

backend_dir = Path("D:/new idea project/tameerai/backend")
ai_test_files = [
    "tests/test_ai_core.py",
    "tests/test_chat_and_rag_models.py",
    "tests/test_chat_api.py",
    "tests/test_chat_hardening_and_integration.py",
    "tests/test_gemini_and_domain_guard.py",
    "tests/test_rag_foundation.py",
    "tests/test_construction_100_benchmark.py",
    "tests/test_construction_intelligence_3f.py",
    "tests/test_construction_safety_and_routing_3g.py",
    "tests/test_structural_safety_3g.py",
    "tests/test_grounded_evidence_and_accuracy_3g.py",
    "tests/test_grounded_adversarial_validation_3g.py",
    "tests/test_grounded_reliability_hardening_3g.py",
    "tests/test_document_extraction.py",
    "tests/test_documents_api.py",
]

for tf in ai_test_files:
    p = backend_dir / tf
    text = p.read_text(encoding="utf-8")
    doc_match = re.search(r'"""(.*?)"""', text, re.DOTALL)
    doc = doc_match.group(1).strip() if doc_match else "No docstring"
    first_lines = "\n    ".join([line.strip() for line in doc.splitlines()[:6] if line.strip()])
    test_funcs = re.findall(r'def (test_[a-zA-Z0-9_]+)', text)
    print(f"\n=== {tf} ({len(test_funcs)} tests) ===")
    print(f"    {first_lines}")

