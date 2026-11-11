import sys
import os
import json
import urllib.request
import urllib.error
import uuid

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from app.main import app

def build_inventory():
    paths = app.openapi().get("paths", {})
    mutation_routes = []
    for path, methods in sorted(paths.items()):
        for method, spec in methods.items():
            if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
                mutation_routes.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": spec.get("summary", ""),
                    "tags": spec.get("tags", []),
                    "security": spec.get("security", []),
                })
    return mutation_routes

def test_routes():
    inventory = build_inventory()
    print(f"Total Mutation Routes to Document: {len(inventory)}")

    # We will format this into a clean structured table
    # Set up Tenant A and Tenant B tokens
    BASE_URL = "http://127.0.0.1:8000"
    
    def req(m, p, h=None, b=None):
        if h is None: h = {}
        data = None
        if b is not None:
            data = json.dumps(b).encode('utf-8')
            h["Content-Type"] = "application/json"
        request = urllib.request.Request(f"{BASE_URL}{p}", data=data, headers=h, method=m)
        try:
            with urllib.request.urlopen(request) as resp:
                return resp.status, resp.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8')
        except Exception as exc:
            return 0, str(exc)

    # Setup Tenant A & B
    uid = uuid.uuid4().hex[:6]
    email_a = f"route_ten_a_{uid}@tameerai.pk"
    email_b = f"route_ten_b_{uid}@tameerai.pk"
    pwd = "Password123!#"

    req("POST", "/api/v1/auth/register", b={"email": email_a, "password": pwd, "full_name": "Ten A", "role": "engineer"})
    _, l_a = req("POST", "/api/v1/auth/login", b={"email": email_a, "password": pwd})
    token_a = json.loads(l_a).get("accessToken")

    req("POST", "/api/v1/auth/register", b={"email": email_b, "password": pwd, "full_name": "Ten B", "role": "contractor"})
    _, l_b = req("POST", "/api/v1/auth/login", b={"email": email_b, "password": pwd})
    token_b = json.loads(l_b).get("accessToken")

    # Create project for Tenant A
    _, p_a_raw = req("POST", "/api/v1/projects", h={"Authorization": f"Bearer {token_a}"}, b={"name": "Inv Proj", "location": "Lahore", "city": "Lahore"})
    proj_a_id = json.loads(p_a_raw).get("uuid")

    print(f"Setup complete: Proj A = {proj_a_id}")

    results = []
    for r in inventory:
        m = r["method"]
        p = r["path"]
        
        # Replace route variables
        test_path = p.replace("{project_id}", str(proj_a_id))
        test_path = test_path.replace("{id}", str(proj_a_id))
        test_path = test_path.replace("{session_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{document_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{audit_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{finding_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{analysis_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{card_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{item_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{job_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{member_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{report_id}", str(uuid.uuid4()))
        test_path = test_path.replace("{quote_id}", str(uuid.uuid4()))

        # Determine payload
        payload = {}
        if "login" in p: payload = {"email": "x@x.com", "password": "wrong"}
        elif "register" in p: payload = {"email": "x@x.com", "password": "x", "full_name": "x", "role": "engineer"}
        elif "refresh" in p: payload = {"refresh_token": "invalid"}
        elif "evaluate" in p: payload = {"building_type": "commercial", "number_of_floors": 4, "soil_type": "medium", "seismic_zone": "2B", "city": "Lahore", "structural_system": "reinforced_concrete"}
        elif "verify-pec" in p: payload = {"pec_registration_number": "PEC-CIVIL-44129"}
        elif "projects" in p and m == "POST": payload = {"name": "Test P", "location": "Lahore", "city": "Lahore"}
        elif "projects" in p and m == "PATCH": payload = {"name": "Updated P"}
        elif "compliance-audits" in p and m == "POST": payload = {"rule_standard": "PBC_2021"}
        elif "contract-analyses" in p and m == "POST": payload = {"contract_title": "Red Book", "raw_text": "Sample text"}
        elif "reports" in p and m == "POST": payload = {"report_title": "Exec Report", "report_type": "executive_summary"}

        # Anon test
        s_anon, resp_anon = req(m, test_path, b=payload if m in ["POST", "PUT", "PATCH"] else None)
        # Invalid test
        s_inv, resp_inv = req(m, test_path, h={"Authorization": "Bearer invalid.token.xyz"}, b=payload if m in ["POST", "PUT", "PATCH"] else None)
        # Cross-tenant test (Tenant B attempting operation on Tenant A project)
        s_cross, resp_cross = req(m, test_path, h={"Authorization": f"Bearer {token_b}"}, b=payload if m in ["POST", "PUT", "PATCH"] else None)

        is_public = "auth" in p or "evaluate" in p or "verify-pec" in p or p == "/projects" and m == "POST" and "api" not in p
        auth_req = "Public" if is_public else "JWT Required"
        ten_scope = "Tenant Scoped" if "{project_id}" in p or "{id}" in p else ("User Scoped" if "users" in p or "chat" in p else "Global")

        results.append({
            "method": m,
            "path": p,
            "auth": auth_req,
            "scope": ten_scope,
            "anon": s_anon,
            "inv": s_inv,
            "cross": s_cross,
        })

    print(f"\nSuccessfully evaluated all {len(results)} mutation routes!")
    # Print sample
    for r in results[:10]:
        print(f"{r['method']:6} {r['path']:50} | Anon: {r['anon']} | Inv: {r['inv']} | Cross: {r['cross']}")

if __name__ == "__main__":
    test_routes()
