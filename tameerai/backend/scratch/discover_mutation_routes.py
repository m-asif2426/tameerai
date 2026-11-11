"""
Discover all registered mutation endpoints in FastAPI OpenAPI schema.
"""
import urllib.request
import json

def discover():
    schema = None
    for url in ["http://127.0.0.1:8000/api/v1/openapi.json", "http://127.0.0.1:8000/openapi.json"]:
        try:
            with urllib.request.urlopen(url) as resp:
                schema = json.loads(resp.read().decode("utf-8"))
                print(f"Loaded OpenAPI from {url}")
                break
        except Exception as e:
            pass

    if not schema:
        # Fallback to direct app inspection
        from app.main import app
        schema = app.openapi()
        print("Generated OpenAPI directly from app.openapi()")

    paths = schema.get("paths", {})
    mutations = []
    for path, methods in sorted(paths.items()):
        for method, details in methods.items():
            if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
                mutations.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", ""),
                    "tags": details.get("tags", []),
                    "security": details.get("security", [])
                })

    print(f"Total Mutation Endpoints Registered: {len(mutations)}")
    for m in mutations:
        sec = "PROTECTED" if m["security"] else "PUBLIC/NONE"
        print(f"[{m['method']:<6}] {m['path']:<50} | {sec:<10} | {m['summary']}")

if __name__ == "__main__":
    discover()
