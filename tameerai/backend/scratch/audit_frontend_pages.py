import os
import re

PAGES = [
    ("Homepage", r"d:\new idea project\tameerai\frontend\src\app\page.tsx"),
    ("Landing MaterialRates", r"d:\new idea project\tameerai\frontend\src\components\landing\MaterialRatesSection.tsx"),
    ("Dashboard", r"d:\new idea project\tameerai\frontend\src\app\dashboard\page.tsx"),
    ("Projects", r"d:\new idea project\tameerai\frontend\src\app\dashboard\projects\page.tsx"),
    ("Project Details", r"d:\new idea project\tameerai\frontend\src\app\dashboard\projects\[id]\page.tsx"),
    ("Material Rates", r"d:\new idea project\tameerai\frontend\src\app\dashboard\costs\page.tsx"),
    ("Structural Safety", r"d:\new idea project\tameerai\frontend\src\app\dashboard\safety\page.tsx"),
    ("Regulations", r"d:\new idea project\tameerai\frontend\src\app\dashboard\regulations\page.tsx"),
    ("Compliance", r"d:\new idea project\tameerai\frontend\src\app\dashboard\compliance\page.tsx"),
    ("Contracts", r"d:\new idea project\tameerai\frontend\src\app\dashboard\contracts\page.tsx"),
    ("AI Assistant", r"d:\new idea project\tameerai\frontend\src\app\dashboard\ai-assistant\page.tsx"),
    ("Audit", r"d:\new idea project\tameerai\frontend\src\app\dashboard\audit\page.tsx"),
    ("Reports", r"d:\new idea project\tameerai\frontend\src\app\dashboard\reports\page.tsx"),
    ("Settings", r"d:\new idea project\tameerai\frontend\src\app\dashboard\settings\page.tsx"),
]

def audit_file(name, path):
    if not os.path.exists(path):
        print(f"[{name}] File NOT found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    services_used = re.findall(r'import\s+\{([^}]+)\}\s+from\s+["\']@/services/([^"\']+)["\']', content)
    has_loading = "isLoading" in content or "loading" in content.lower()
    has_error = "error" in content.lower()
    has_empty = "empty" in content.lower() or "no " in content.lower() or "not found" in content.lower()
    
    # Check for hardcoded mock arrays (e.g. const mock = [...], dummyData = [...], etc.)
    mock_matches = re.findall(r'(const|let|var)\s+([a-zA-Z0-9_]*(mock|dummy|fake|sample|static)[a-zA-Z0-9_]*)\s*=', content, re.IGNORECASE)

    print(f"\n=======================================================")
    print(f"PAGE: {name} ({os.path.basename(path)})")
    print(f"Path: {path} ({len(lines)} lines)")
    print(f"Services: {services_used}")
    print(f"Mock arrays detected: {mock_matches}")
    print(f"Loading state present: {has_loading}")
    print(f"Error state present: {has_error}")
    print(f"Empty state present: {has_empty}")

def main():
    for name, path in PAGES:
        audit_file(name, path)

if __name__ == "__main__":
    main()

