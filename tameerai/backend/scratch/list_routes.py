import sys
sys.path.insert(0, r"d:\new idea project\tameerai\backend")
from app.main import app
from fastapi.routing import APIRoute

print(f"Total routes in app: {len(app.routes)}")
for r in app.routes:
    if isinstance(r, APIRoute):
        methods = list(r.methods)
        print(f"{methods} {r.path} -> {r.name}")

