import sys
from pathlib import Path
import inspect

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

def inspect_module(mod_name):
    try:
        mod = __import__(mod_name, fromlist=["*"])
        print(f"\n=== Module: {mod_name} ===")
        classes = [name for name, cls in inspect.getmembers(mod, inspect.isclass) if cls.__module__ == mod_name]
        funcs = [name for name, fn in inspect.getmembers(mod, inspect.isfunction) if fn.__module__ == mod_name]
        print(f"  Classes ({len(classes)}): {classes}")
        print(f"  Functions ({len(funcs)}): {funcs}")
        if hasattr(mod, "__doc__") and mod.__doc__:
            print(f"  Docstring: {mod.__doc__.strip().splitlines()[0]}")
    except Exception as e:
        print(f"\n=== Module: {mod_name} (ERROR: {e}) ===")

modules = [
    "app.models.chat",
    "app.models.document",
    "app.models.knowledge",
    "app.services.chat_service",
    "app.api.v1.endpoints.chat",
    "app.ai.workflow.construction_chat",
    "app.ai.guardrails.intent",
    "app.ai.guardrails.domain_guard",
    "app.ai.guardrails.structural_safety",
    "app.ai.guardrails.context_engine",
    "app.ai.providers.factory",
    "app.ai.providers.gemini_provider",
    "app.ai.retrieval.service",
    "app.ai.validation.grounded_policy",
]

for m in modules:
    inspect_module(m)

