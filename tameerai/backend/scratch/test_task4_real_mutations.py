"""
TASK 4 — REAL API MUTATION SECURITY VERIFICATION
Tests genuine registered mutation routes on http://127.0.0.1:8000/api/v1
- Anonymous rejection (401)
- Invalid bearer (401)
- Valid tenant creation (201)
- Cross-tenant read isolation (404)
- Cross-tenant mutation isolation (404)
- Public snapshot field sanitization (200)
"""

import urllib.request
import urllib.error
import json
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def make_req(endpoint, method="GET", headers=None, body=None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}, resp.headers
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed, e.headers

def run_tests():
    print("="*60)
    print("TASK 4 — REAL API MUTATION SECURITY TESTS")
    print("="*60)

    # 1. Anonymous rejection on POST /projects
    status_code, body, _ = make_req("/projects", method="POST", body={"name": "Illegal Anon Plaza"})
    assert status_code == 401, f"Expected 401, got {status_code}: {body}"
    print(f"[PASS] 1. Anonymous POST /projects rejected: HTTP {status_code} ({body.get('detail')})")

    # 2. Invalid Bearer token on POST /projects
    status_code, body, _ = make_req(
        "/projects",
        method="POST",
        headers={"Authorization": "Bearer invalid.fake.token"},
        body={"name": "Illegal Bearer Plaza"}
    )
    assert status_code == 401, f"Expected 401, got {status_code}: {body}"
    print(f"[PASS] 2. Invalid Bearer POST /projects rejected: HTTP {status_code} ({body.get('detail')})")

    # 3. Create two distinct tenants for multi-tenant isolation testing
    t1_email = f"task4_tenant_a_{uuid.uuid4().hex[:6]}@tameerai.pk"
    t2_email = f"task4_tenant_b_{uuid.uuid4().hex[:6]}@tameerai.pk"
    pwd = "SecuredPassword99#!"

    # Register Tenant A
    status_a, _, _ = make_req("/auth/register", method="POST", body={
        "email": t1_email,
        "password": pwd,
        "full_name": "Tenant A Engineer",
        "role": "engineer",
        "company": "Tenant A Corp"
    })
    assert status_a == 201, f"Register A failed: {status_a}"

    # Login Tenant A
    status_login_a, login_a_data, _ = make_req("/auth/login", method="POST", body={
        "email": t1_email,
        "password": pwd
    })
    assert status_login_a == 200, f"Login A failed: {status_login_a}"
    token_a = login_a_data.get("accessToken") or login_a_data.get("access_token")

    # Register Tenant B
    status_b, _, _ = make_req("/auth/register", method="POST", body={
        "email": t2_email,
        "password": pwd,
        "full_name": "Tenant B Contractor",
        "role": "contractor",
        "company": "Tenant B Corp"
    })
    assert status_b == 201, f"Register B failed: {status_b}"

    # Login Tenant B
    status_login_b, login_b_data, _ = make_req("/auth/login", method="POST", body={
        "email": t2_email,
        "password": pwd
    })
    assert status_login_b == 200, f"Login B failed: {status_login_b}"
    token_b = login_b_data.get("accessToken") or login_b_data.get("access_token")
    print(f"[PASS] 3. Registered & Authenticated Tenant A and Tenant B successfully (tokens masked).")

    # 4. Valid Tenant A Project Creation (POST /projects)
    status_proj_a, proj_a, _ = make_req(
        "/projects",
        method="POST",
        headers={"Authorization": f"Bearer {token_a}"},
        body={
            "name": "Tenant A Highrise Commercial",
            "location": "Gulberg III, Lahore",
            "city": "Lahore",
            "type": "Commercial",
            "budgetCrore": 5.0,
            "floors": 12,
            "areaSqft": "45,000 sq ft"
        }
    )
    assert status_proj_a == 201, f"Expected 201, got {status_proj_a}: {proj_a}"
    project_id_a = proj_a["id"]
    print(f"[PASS] 4. Valid Tenant A creation: HTTP {status_proj_a} Project ID: {project_id_a} Code: {proj_a.get('code')}")

    # 5. Cross-Tenant Read: Tenant B attempts to read Tenant A's project
    status_read, body_read, _ = make_req(
        f"/projects/{project_id_a}",
        method="GET",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    # Must be 404 to avoid enumeration
    assert status_read == 404, f"Expected 404 for cross-tenant read, got {status_read}: {body_read}"
    print(f"[PASS] 5. Cross-Tenant Read rejected: HTTP {status_read} (Non-enumerable 404: {body_read.get('detail')})")

    # 6. Cross-Tenant Mutation: Tenant B attempts to PATCH Tenant A's project
    status_patch, body_patch, _ = make_req(
        f"/projects/{project_id_a}",
        method="PATCH",
        headers={"Authorization": f"Bearer {token_b}"},
        body={"name": "Hacked By Tenant B"}
    )
    # Must be 404 (non-enumerable) or 403
    assert status_patch in [403, 404], f"Expected 403/404, got {status_patch}: {body_patch}"
    print(f"[PASS] 6. Cross-Tenant Mutation rejected: HTTP {status_patch} ({body_patch.get('detail')})")

    # 7. Cross-Tenant Delete: Tenant B attempts to DELETE Tenant A's project
    status_del, body_del, _ = make_req(
        f"/projects/{project_id_a}",
        method="DELETE",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert status_del in [403, 404], f"Expected 403/404, got {status_del}: {body_del}"
    print(f"[PASS] 7. Cross-Tenant Delete rejected: HTTP {status_del} ({body_del.get('detail')})")

    # 8. Public Snapshot Field Sanitization (GET /material-rates/snapshots)
    status_snap, snap_data, _ = make_req("/material-rates/snapshots?city=Lahore", method="GET")
    assert status_snap == 200, f"Expected 200, got {status_snap}"
    snapshots = snap_data if isinstance(snap_data, list) else snap_data.get("snapshots", [])
    assert len(snapshots) > 0, "No snapshots returned"
    
    # Verify field whitelist
    forbidden_fields = {"raw_price", "raw_unit", "tenant_id", "user_id", "hashed_password", "source_url", "email"}

    all_keys = set()
    for s in snapshots:
        all_keys.update(s.keys())
        leaked = set(s.keys()) & forbidden_fields
        assert not leaked, f"Leaked sensitive/internal fields: {leaked}"
        
    print(f"[PASS] 8. Public Snapshot Sanitized: HTTP 200, {len(snapshots)} items returned.")
    print(f"       Present public keys: {sorted(list(all_keys))}")
    print(f"       Zero forbidden internal fields detected.")
    print("="*60)
    print("TASK 4 EVIDENCE COLLECTION: 100% PASS")
    print("="*60)

if __name__ == "__main__":
    run_tests()
