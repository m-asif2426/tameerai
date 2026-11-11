import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings

print("=== Task E: Safety & Environment Configuration Verification ===")
print(f"ENABLE_MATERIAL_RATE_COLLECTION: {settings.ENABLE_MATERIAL_RATE_COLLECTION} (Expected: False)")
print(f"ENABLE_GEMINI_API: {settings.ENABLE_GEMINI_API} (Expected: False)")
print(f"ENABLE_AI_FEATURES: {settings.ENABLE_AI_FEATURES} (Expected: False)")
assert settings.ENABLE_MATERIAL_RATE_COLLECTION is False, "Safety violation: ENABLE_MATERIAL_RATE_COLLECTION must be False"
assert settings.ENABLE_GEMINI_API is False, "Safety violation: ENABLE_GEMINI_API must be False"
assert settings.ENABLE_AI_FEATURES is False, "Safety violation: ENABLE_AI_FEATURES must be False"
print("All safety flags verified as FALSE.")

