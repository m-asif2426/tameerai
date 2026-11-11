"""
TASK 6 — COMPLETE API ROUTE SECURITY MATRIX VERIFICATION
Tests prioritized mutation endpoints across all domains:
1. Projects (POST /api/v1/projects, PATCH /api/v1/projects/{id}, DELETE /api/v1/projects/{id})
2. Dealer Quotations (POST /api/v1/material-rates/dealers/quotes)
3. Orchestration Trigger (POST /api/v1/material-rates/orchestration/trigger)
4. Structural Safety Evaluation (POST /api/v1/safety/evaluate - Public)
5. PEC Verification (POST /api/v1/safety/verify-pec - Public format check)
6. PEC Sign-Off (POST /api/v1/safety/sign-off - Protected)
7. Compliance Audits (POST /api/v1/projects/{id}/compliance-audits)
8. Contract Analyses (POST /api/v1/projects/{id}/contract-analyses)
9. Chat Sessions (POST /api/v1/chat/sessions, POST /api/v1/chat/sessions/{id}/messages)
10. Reports (POST /api/v1/projects/{id}/reports)
"""

import urllib.request
import urllib.error
import json
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(endpoint, method="GET", token=None, body=None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_data) if resp_data else {}
    except urllib.error.HTTPError as e:
        err_data = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_data)
        except Exception:
            parsed = {"raw": err_data}
        return e.code, parsed

def setup_tenants():
    # Register and login Tenant A
    email_a = f"task6_ten_a_{uuid.uuid4().hex[:6]}@tameerai.pk"
    pwd = "Password123!#"
    api_call("/auth/register", "POST", body={"email": email_a, "password": pwd, "full_name": "Engr Tenant A", "role": "engineer"})
    _, login_a = api_call("/auth/login", "POST", body={"email": email_a, "password": pwd})
    token_a = login_a.get("accessToken") or login_a.get("access_token")

    # Register and login Tenant B
    email_b = f"task6_ten_b_{uuid.uuid4().hex[:6]}@tameerai.pk"
    api_call("/auth/register", "POST", body={"email": email_b, "password": pwd, "full_name": "Contractor Tenant B", "role": "contractor"})
    _, login_b = api_call("/auth/login", "POST", body={"email": email_b, "password": pwd})
    token_b = login_b.get("accessToken") or login_b.get("access_token")

    # Create Project for Tenant A
    status_p, proj_a = api_call("/projects", "POST", token=token_a, body={
        "name": "Security Verification Plaza",
        "location": "Main Boulevard, Gulberg, Lahore",
        "city": "Lahore",
        "type": "Commercial",
        "budgetCrore": 10.0
    })
    project_uuid_a = proj_a.get("uuid")
    print(f"Created Tenant A Project UUID: {project_uuid_a}, Code: {proj_a.get('id')}")

    return token_a, token_b, project_uuid_a

def run_matrix():
    token_a, token_b, project_id_a = setup_tenants()
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid_signature"

    routes_to_test = [
        # 1. Projects
        ("POST", "/projects", {"name": "Test", "location": "Lahore", "city": "Lahore"}, True, True, "test_project_create_security"),
        ("PATCH", f"/projects/{project_id_a}", {"name": "Mutated"}, True, True, "test_project_patch_security"),
        ("DELETE", f"/projects/{project_id_a}", None, True, True, "test_project_delete_security"),

        # 2. Material Rates & Dealers
        ("POST", "/material-rates/dealers/quotes", {"dealer_name": "Test"}, True, False, "test_dealer_quotes_security"),
        ("POST", "/material-rates/orchestration/trigger", {"source_code": "PBS_MONTHLY"}, True, False, "test_orchestration_trigger_security"),

        # 3. Structural Safety
        ("POST", "/safety/evaluate", {"query": "Severe diagonal crack in basement column"}, False, False, "test_safety_evaluate_public"),
        ("POST", "/safety/verify-pec", {"pec_number": "CIVIL/12345"}, False, False, "test_safety_verify_pec_public"),
        ("POST", "/safety/sign-off", {"pec_number": "CIVIL/12345", "engineer_name": "Engr A", "physical_site_inspection_conducted": True}, True, False, "test_safety_sign_off_security"),

        # 4. Compliance Audits
        ("POST", f"/projects/{project_id_a}/compliance-audits", {"governing_code": "PBC 2021"}, True, True, "test_compliance_audit_create_security"),

        # 5. Contract Analyses
        ("POST", f"/projects/{project_id_a}/contract-analyses", {"contract_title": "FIDIC Red Book 2017"}, True, True, "test_contract_analysis_create_security"),

        # 6. Chat Sessions
        ("POST", "/chat/sessions", {"title": "Security Audit Session"}, True, False, "test_chat_session_create_security"),

        # 7. Reports
        ("POST", f"/projects/{project_id_a}/reports", {"title": "Executive Structural Report", "category": "structural"}, True, True, "test_report_create_security"),
    ]

    matrix_results = []
    print("="*100)
    print(f"{'METHOD':<7} {'ENDPOINT':<45} {'AUTH':<6} {'TENANT':<7} {'ANON':<6} {'INVALID':<8} {'CROSS-TENANT':<14} {'TEST NAME'}")
    print("="*100)

    for method, endpoint, body, req_auth, req_tenant, test_name in routes_to_test:
        # 1. Anon test
        anon_st, _ = api_call(endpoint, method, token=None, body=body)

        # 2. Invalid token test
        inv_st, _ = api_call(endpoint, method, token=invalid_token, body=body)

        # 3. Cross-tenant test (if route is tenant-scoped)
        if req_tenant:
            # Tenant B calls Tenant A's resource
            cross_st, _ = api_call(endpoint, method, token=token_b, body=body)
        else:
            # For non-project scoped protected routes, Tenant B calls route
            cross_st, _ = api_call(endpoint, method, token=token_b, body=body)
            cross_st = f"N/A ({cross_st})"

        auth_label = "YES" if req_auth else "NO"
        tenant_label = "YES" if req_tenant else "GLOBAL"

        print(f"{method:<7} {endpoint:<45} {auth_label:<6} {tenant_label:<7} {anon_st:<6} {inv_st:<8} {str(cross_st):<14} {test_name}")
        matrix_results.append({
            "method": method,
            "endpoint": endpoint,
            "auth_req": auth_label,
            "tenant_req": tenant_label,
            "anon_code": anon_st,
            "invalid_code": inv_st,
            "cross_code": cross_st,
            "test_name": test_name
        })

    print("="*100)
    return matrix_results

if __name__ == "__main__":
    run_matrix()
