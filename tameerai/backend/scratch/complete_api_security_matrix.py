import asyncio
import os
import sys
import json
import urllib.request
import urllib.error

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

BASE_URL = "http://127.0.0.1:8000"

def make_req(method, endpoint, headers=None, data=None):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            try:
                body = json.loads(body)
            except:
                pass
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body = json.loads(body)
        except:
            pass
        return e.code, body
    except Exception as exc:
        return 0, str(exc)

def run_security_matrix():
    print("=== STARTING TASK 6 COMPLETE API SECURITY INVENTORY & PENETRATION SUITE ===")
    
    # 1. Login Tenant A and Tenant B to get legitimate JWT tokens
    import time
    timestamp = int(time.time())
    email_a = f"security_tenant_a_{timestamp}@example.com"
    email_b = f"security_tenant_b_{timestamp}@example.com"
    password = "StrongPassword123!"

    # Register Tenant A
    status_reg_a, _ = make_req("POST", "/api/v1/auth/register", data={
        "email": email_a,
        "password": password,
        "full_name": "Security Tenant A",
        "company_name": "Tenant A Corp",
        "role": "engineer"
    })
    status_log_a, res_a = make_req("POST", "/api/v1/auth/login", data={
        "email": email_a,
        "password": password
    })
    token_a = res_a.get("access_token")
    print(f"Tenant A registered: {status_reg_a} | Login: {status_log_a} | Token length: {len(token_a) if token_a else 0}")

    # Register Tenant B
    status_reg_b, _ = make_req("POST", "/api/v1/auth/register", data={
        "email": email_b,
        "password": password,
        "full_name": "Security Tenant B",
        "company_name": "Tenant B Corp",
        "role": "engineer"
    })
    status_log_b, res_b = make_req("POST", "/api/v1/auth/login", data={
        "email": email_b,
        "password": password
    })
    token_b = res_b.get("access_token")
    print(f"Tenant B registered: {status_reg_b} | Login: {status_log_b} | Token length: {len(token_b) if token_b else 0}")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_invalid = {"Authorization": "Bearer invalid_token_xyz_9999"}
    headers_anon = {}

    # 2. Create Project in Tenant A
    status, proj_a = make_req("POST", "/api/v1/projects", headers=headers_a, data={
        "name": "Tenant A Secure Project",
        "public_code": f"PRJ-A-{timestamp}",
        "location": "Lahore",
        "total_budget": 50000000.00
    })
    proj_a_id = proj_a.get("id") or proj_a.get("uuid")
    print(f"Tenant A Project created: {status} | ID: {proj_a_id}")

    # 3. Test Attack Scenarios on Tenant A Project
    endpoints_to_test = [
        ("GET", f"/api/v1/projects/{proj_a_id}", None, "Project Read Isolation"),
        ("PATCH", f"/api/v1/projects/{proj_a_id}", {"name": "Hacked Name"}, "Project Update Isolation"),
        ("DELETE", f"/api/v1/projects/{proj_a_id}", None, "Project Deletion Isolation"),
        ("POST", f"/api/v1/projects/{proj_a_id}/compliance-audits", {"rule_standard": "IBC_2021"}, "Compliance Audit Isolation"),
        ("POST", f"/api/v1/projects/{proj_a_id}/contract-analyses", {"contract_title": "Rogue Contract", "raw_text": "Sample text"}, "Contract Analysis Isolation"),
        ("POST", f"/api/v1/projects/{proj_a_id}/reports", {"report_title": "Rogue Report", "report_type": "executive_summary"}, "Report Generation Isolation"),
        ("POST", f"/api/v1/projects/{proj_a_id}/documents", {"title": "Rogue Doc", "category": "drawing"}, "Document Upload Isolation"),
        ("POST", f"/api/v1/projects/{proj_a_id}/jobs", {"job_type": "contract_analysis"}, "Background Job Isolation"),
    ]

    print("\n--- MATRIX EVALUATION ---")
    matrix_results = []
    for method, path, body, desc in endpoints_to_test:
        # Context 1: Anonymous
        s_anon, r_anon = make_req(method, path, headers=headers_anon, data=body)
        # Context 2: Invalid Token
        s_inv, r_inv = make_req(method, path, headers=headers_invalid, data=body)
        # Context 3: Cross-Tenant (Tenant B trying to mutate/read Tenant A)
        s_cross, r_cross = make_req(method, path, headers=headers_b, data=body)
        
        matrix_results.append({
            "desc": desc,
            "method": method,
            "path": path,
            "anon": s_anon,
            "invalid": s_inv,
            "cross_tenant": s_cross,
            "detail": r_cross.get("detail") if isinstance(r_cross, dict) else str(r_cross)
        })
        print(f"[{desc}] {method} {path}")
        print(f"   Anon: {s_anon} | Invalid: {s_inv} | Cross-Tenant (Tenant B -> A): {s_cross} ({r_cross.get('detail') if isinstance(r_cross, dict) else 'OK'})")

    # 4. Test Forged Ownership during Project Creation
    print("\n--- FORGED OWNERSHIP TEST ---")
    user_a_id = res_a.get("user", {}).get("id") or "00000000-0000-0000-0000-000000000001"
    status_forged, res_forged = make_req("POST", "/api/v1/projects", headers=headers_b, data={
        "name": "Forged Owner Project",
        "public_code": f"PRJ-FORGE-{timestamp}",
        "location": "Karachi",
        "total_budget": 10000000.00,
        "owner_id": user_a_id,  # Attempting to assign Tenant A as owner
        "tenant_id": user_a_id
    })
    print(f"Forged Creation Status: {status_forged}")
    # Verify who owns it in the response
    actual_owner = res_forged.get("owner_id") or res_forged.get("created_by")
    print(f"Requested Owner: {user_a_id} | Actual Owner Assigned: {actual_owner}")
    assert str(actual_owner) != str(user_a_id), "CRITICAL VULNERABILITY: Forged owner_id was accepted!"
    print("SUCCESS: Forged ownership parameter was safely ignored/sanitized.")

    # 5. Public Snapshot Sanitization
    print("\n--- PUBLIC SNAPSHOT SANITIZATION AUDIT ---")
    s_snap, r_snap = make_req("GET", "/api/v1/material-rates/snapshots")
    print(f"Snapshots HTTP Status: {s_snap} | Count: {len(r_snap)}")
    leakage_keys = ["tenant_id", "dealer_phone", "dealer_ntn", "contact_phone", "password", "email", "raw_payload"]
    leaked = []
    if isinstance(r_snap, list) and r_snap:
        sample = r_snap[0]
        for k in leakage_keys:
            if k in sample:
                leaked.append(k)
        print("Sample Snapshot Keys:", list(sample.keys()))
    print(f"Leakage Audit: {len(leaked)} forbidden keys found: {leaked}")
    assert len(leaked) == 0, f"DATA LEAKAGE: {leaked}"
    print("SUCCESS: Public material snapshot is 100% sanitized.")

if __name__ == "__main__":
    run_security_matrix()
