import os
import sys
import subprocess
from pathlib import Path

backend_dir = Path("D:/new idea project/tameerai/backend")

# List of AI / Chat test files
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

print("=== Checking Existence of AI Test Files ===")
for tf in ai_test_files:
    p = backend_dir / tf
    print(f"{tf}: {'EXISTS' if p.exists() else 'MISSING'} ({p.stat().st_size if p.exists() else 0} bytes)")

