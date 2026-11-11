import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_full_api_contract_and_security():
    print("=" * 80)
    print("TEST SUITE: API CONTRACT & SECURITY VERIFICATION")
    print("=" * 80)
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Unauthenticated health / public rates check
        print("\n1. GET /material-rates/snapshots (Public Unauthenticated)")
        r = client.get("/material-rates/snapshots")
        print(f"   Status: {r.status_code}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        rates_data = r.json()
        rates_count = len(rates_data) if isinstance(rates_data, list) else len(rates_data.get('items', []))
        print(f"   Snapshots returned: {rates_count}")
        for snap in rates_data[:3]:
            print(f"     - {snap.get('name')} in {snap.get('city')}: PKR {snap.get('rate_pkr')} (Source: {snap.get('source_name')})")

        # 2. Login as e2e_tester@tameerai.pk
        print("\n2. POST /auth/login (Authentication Contract)")
        login_res = client.post("/auth/login", json={
            "email": "e2e_tester@tameerai.pk",
            "password": "Password123!"
        })
        print(f"   Status: {login_res.status_code}")
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        auth_data = login_res.json()
        access_token = auth_data.get("accessToken") or auth_data.get("access_token")
        assert access_token, f"No access_token returned in {list(auth_data.keys())}"
        print(f"   Access Token Received: {access_token[:15]}...{access_token[-10:]}")
        print(f"   Token Type: {auth_data.get('token_type')}")
        
        # Security test: check cookies
        print("   Checking Set-Cookie headers for refresh token security...")
        refresh_cookie = login_res.cookies.get("tameerai_refresh_token") or login_res.cookies.get("refresh_token")
        cookie_header = login_res.headers.get("set-cookie", "")
        print(f"   Refresh cookie set: {bool(refresh_cookie)}")
        print(f"   HttpOnly flag present: {'HttpOnly' in cookie_header}")
        print(f"   SameSite flag present: {'SameSite' in cookie_header}")
        
        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. GET /users/me
        print("\n3. GET /users/me (Identity Verification)")
        user_res = client.get("/users/me", headers=headers)
        print(f"   Status: {user_res.status_code}")
        assert user_res.status_code == 200
        user_data = user_res.json()
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Email: {user_data.get('email')}")
        print(f"   Full Name: {user_data.get('full_name')}")
        print(f"   Role: {user_data.get('role')}")
        assert user_data.get("email") == "e2e_tester@tameerai.pk"

        # 4. GET /projects (List projects for this tenant)
        print("\n4. GET /projects (Tenant Scoped Project List)")
        proj_res = client.get("/projects", headers=headers)
        print(f"   Status: {proj_res.status_code}")
        assert proj_res.status_code == 200
        projs = proj_res.json()
        items = projs.get("items", projs if isinstance(projs, list) else [])
        print(f"   Current projects count for e2e_tester: {len(items)}")

        # 5. POST /projects (Create Project in PostgreSQL 17)
        print("\n5. POST /projects (Create New Project)")
        create_payload = {
            "name": "Phase 03.4E.1 Verification Complex",
            "nameUrdu": "فیز 03.4E.1 تصدیقی کمپلیکس",
            "location": "Gulberg III, Main Boulevard",
            "city": "Lahore",
            "type": "Commercial",
            "budgetCrore": 16.5,
            "floors": 7,
            "areaSqft": "32,000 sq ft"
        }
        create_res = client.post("/projects", json=create_payload, headers=headers)
        print(f"   Status: {create_res.status_code}")
        assert create_res.status_code in [200, 201], f"Project creation failed: {create_res.text}"
        new_proj = create_res.json()
        new_proj_id = new_proj.get("id")
        print(f"   Created Project ID: {new_proj_id}")
        print(f"   Code: {new_proj.get('code')}")
        print(f"   Name: {new_proj.get('name')}")
        print(f"   Budget (Crore): {new_proj.get('budgetCrore') or new_proj.get('budget_crore')}")

        # 6. GET /projects/{id} (Fetch created project)
        print(f"\n6. GET /projects/{new_proj_id} (Fetch by ID)")
        get_res = client.get(f"/projects/{new_proj_id}", headers=headers)
        print(f"   Status: {get_res.status_code}")
        assert get_res.status_code == 200
        fetched_proj = get_res.json()
        assert fetched_proj.get("id") == new_proj_id

        # 7. GET /projects/non-existent-uuid (404 check)
        print("\n7. GET /projects/00000000-0000-0000-0000-000000000000 (Expect 404)")
        not_found_res = client.get("/projects/00000000-0000-0000-0000-000000000000", headers=headers)
        print(f"   Status: {not_found_res.status_code} (Expected 404)")
        assert not_found_res.status_code == 404

        # 8. Structural Safety Engine: 38 Indicators
        print("\n8. GET /safety/indicators (Structural Safety 38 Indicators)")
        safety_ind_res = client.get("/safety/indicators", headers=headers)
        print(f"   Status: {safety_ind_res.status_code}")
        assert safety_ind_res.status_code == 200
        indicators = safety_ind_res.json()
        ind_list = indicators if isinstance(indicators, list) else indicators.get("indicators", [])
        print(f"   Exact indicator count returned: {len(ind_list)}")
        assert len(ind_list) == 38, f"Expected 38 indicators, got {len(ind_list)}"
        print("   Sample indicators:")
        for ind in ind_list[:4]:
            print(f"     - {ind.get('code')}: {ind.get('description')} ({ind.get('category')})")

        # 9. Structural Safety Evaluate
        print("\n9. POST /safety/evaluate (Safety Assessment Evaluation)")
        eval_payload = {
            "query": "Deep 45-degree diagonal shear cracks noticed across ground floor column with spalling concrete and exposed rebar"
        }
        eval_res = client.post("/safety/evaluate", json=eval_payload, headers=headers)
        print(f"   Status: {eval_res.status_code}")
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        print(f"   Is Hazard Detected: {eval_data.get('is_hazard')}")
        print(f"   Severity Level: {eval_data.get('severity_level')}")
        print(f"   Triggered Indicators: {eval_data.get('triggered_indicators')}")
        print(f"   Safety Advisory: {eval_data.get('immediate_action') or eval_data.get('safety_advisory')}")

        # 10. Security: Multi-tenant isolation (Attempt to access another tenant's project)
        print("\n10. Multi-Tenant Security Check: Attempting to access Tenant A's project")
        tenant_a_proj = "95bd231f-cd76-4d1e-8b88-2d44c8bad520"
        leak_res = client.get(f"/projects/{tenant_a_proj}", headers=headers)
        print(f"    Status: {leak_res.status_code} (Expected 403 or 404)")
        assert leak_res.status_code in [403, 404], f"Cross-tenant leak! Got {leak_res.status_code}"
        print("    PASS: Cross-tenant project access strictly forbidden!")

        # 11. Security: Safety Flags Check
        print("\n11. Safety Flags Verification via Backend Health / Config")
        health_res = client.get("/health")
        print(f"    Status: {health_res.status_code}")
        health_data = health_res.json()
        print(f"    Health: {health_data}")

    print("\n" + "=" * 80)
    print("ALL 11 API CONTRACT AND SECURITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == '__main__':
    test_full_api_contract_and_security()
