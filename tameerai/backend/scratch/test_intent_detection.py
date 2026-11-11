import sys
from pathlib import Path

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

from app.ai.guardrails.normalizer import TextNormalizer
from app.ai.guardrails.intent import ConstructionIntent, ConstructionIntentDetector

test_queries = [
    "What is today's cement rate in Lahore?",
    "What is the current steel price in Karachi?",
    "Lahore mein cement ka rate kya hai?",
    "Aaj saria kitne ka mil raha hai?",
    "1000 eenton ki qeemat kitni hai?",
    "Karachi aur Lahore mein cement ke rates compare karo.",
    "لاہور میں سیمنٹ کا آج کا ریٹ کیا ہے؟",
    "کراچی میں سریے کی قیمت کتنی ہے؟",
    "Saria ka rate batao.",
    "Lahore mein.",
    # Benchmark queries that shouldn't change
    "Labor rate per square foot for brick masonry and plastering in Lahore market.",
    "Thekedar ko square foot rate par grey structure contract dena behtar hai ya item rate par?",
    "1000 square feet slab ke liye concrete quantity aur cement bags calculate karain.",
]

for q in test_queries:
    norm = TextNormalizer.normalize(q)
    res = ConstructionIntentDetector.detect_intent(norm)
    print(f"Query: {q}")
    print(f"  Intent: {res.primary_intent.value} | Conf: {res.confidence:.2f} | Signals: {res.matched_intent_signals}")
