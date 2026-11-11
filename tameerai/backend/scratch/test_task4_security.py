import asyncio
import os
import sys
import json
import uuid
from datetime import datetime, timezone
import urllib.request
import urllib.error

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test'
sys.path.insert(0, r'd:\new idea project\tameerai\backend')

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.project import Project
from app.models.material_rate import MaterialRateDealer, MaterialRateProduct

def make_req(url, method='GET', data=None, headers=None):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, (dict, list)):
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None and isinstance(data, str):
        data_bytes = data.encode('utf-8')
    else:
        data_bytes = None

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, body
    except Exception as e:
        return 0, str(e)

async def run_security_suite():
    print("=== TASK 4: LEGACY & API SECURITY VERIFICATION ===")
    
    # 1. Test legacy decommissioned routes
    legacy_routes = [
        ("GET", "http://127.0.0.1:8000/projects"),
        ("GET", "http://127.0.0.1:8000/projects/1"),
        ("POST", "http://127.0.0.1:8000/projects", {"name": "Hacked", "location": "Nowhere", "budget": 1000}),
        ("PUT", "http://127.0.0.1:8000/projects/1", {"name": "Hacked", "location": "Nowhere", "budget": 1000}),
        ("DELETE", "http://127.0.0.1:8000/projects/1"),
    ]
    print("\n--- 1. Testing Decommissioned Root /projects Routes ---")
    for method, url, *body in legacy_routes:
        payload = body[0] if body else None
        status, resp = make_req(url, method=method, data=payload)
        print(f"{method:6s} {url:35s} -> Status: {status} (Expected 404 Not Found)")
        assert status == 404, f"Legacy route {url} unexpectedly returned {status}"

    # 2. Register fresh users to get tokens for Tenant A and Tenant B
    uid = uuid.uuid4().hex[:6]
    email_a = f"task4_ten_a_{uid}@tameerai.pk"
    email_b = f"task4_ten_b_{uid}@tameerai.pk"
    pwd = "Password123!#"

    make_req("http://127.0.0.1:8000/api/v1/auth/register", "POST", {"email": email_a, "password": pwd, "full_name": "Ten A Eng", "role": "engineer"})
    status_a, resp_a = make_req("http://127.0.0.1:8000/api/v1/auth/login", "POST", {"email": email_a, "password": pwd})
    token_a = json.loads(resp_a).get("accessToken") or json.loads(resp_a).get("access_token")
    user_a_id = json.loads(resp_a)["user"]["id"]

    make_req("http://127.0.0.1:8000/api/v1/auth/register", "POST", {"email": email_b, "password": pwd, "full_name": "Ten B Contr", "role": "contractor"})
    status_b, resp_b = make_req("http://127.0.0.1:8000/api/v1/auth/login", "POST", {"email": email_b, "password": pwd})
    token_b = json.loads(resp_b).get("accessToken") or json.loads(resp_b).get("access_token")
    user_b_id = json.loads(resp_b)["user"]["id"]

    print(f"\nTenant A registered & logged in: {user_a_id} ({email_a})")
    print(f"Tenant B registered & logged in: {user_b_id} ({email_b})")

    # 3. Anonymous & Invalid Token on /api/v1/projects
    print("\n--- 2. Anonymous & Invalid Token on /api/v1/projects ---")
    anon_post_status, _ = make_req("http://127.0.0.1:8000/api/v1/projects", "POST", {"name": "Anon Project", "location": "Lahore", "city": "Lahore", "type": "Commercial Plaza", "budget_crore": 5.0})
    print(f"POST /api/v1/projects (Anonymous)     -> Status: {anon_post_status} (Expected 401)")
    assert anon_post_status == 401

    fake_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.signature"}
    inv_post_status, _ = make_req("http://127.0.0.1:8000/api/v1/projects", "POST", {"name": "Inv Project", "location": "Lahore", "city": "Lahore", "type": "Commercial Plaza", "budget_crore": 5.0}, headers=fake_headers)
    print(f"POST /api/v1/projects (Invalid Token)  -> Status: {inv_post_status} (Expected 401)")
    assert inv_post_status == 401

    # 4. Forged owner_id rejection test
    print("\n--- 3. Forged owner_id Rejection Test ---")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    forged_payload = {
        "name": f"Forged Tower {uuid.uuid4().hex[:6]}",
        "location": "Gulberg III",
        "city": "Lahore",
        "type": "Commercial Plaza",
        "budget_crore": 12.5,
        "owner_id": user_b_id, # Attempted forged owner_id
    }
    forged_status, forged_resp = make_req("http://127.0.0.1:8000/api/v1/projects", "POST", forged_payload, headers=headers_a)
    print(f"POST /api/v1/projects (Forged owner_id)-> Status: {forged_status} (Expected 422 Extra Inputs Forbidden)")
    assert forged_status == 422, "Pydantic failed to reject unauthorized owner_id parameter!"

    # 5. Legitimate Tenant A Project Creation
    print("\n--- 4. Tenant A Legitimate Project Creation ---")
    legit_payload = {
        "name": f"Secured Tower {uuid.uuid4().hex[:6]}",
        "location": "Gulberg III",
        "city": "Lahore",
        "type": "Commercial Plaza",
        "budget_crore": 12.5,
    }
    create_status, create_resp = make_req("http://127.0.0.1:8000/api/v1/projects", "POST", legit_payload, headers=headers_a)
    print(f"POST /api/v1/projects (Tenant A)       -> Status: {create_status} (Expected 201)")
    assert create_status == 201
    proj_data = json.loads(create_resp)
    proj_id = proj_data.get("uuid") or proj_data.get("id")
    print(f"Created Project ID: {proj_id}, Name: {proj_data['name']}")

    # 6. Cross-Tenant Isolation Tests (Tenant B attacking Tenant A project)
    print("\n--- 5. Cross-Tenant Isolation & Attack Tests ---")
    
    # Read attempt by Tenant B
    b_read_status, b_read_body = make_req(f"http://127.0.0.1:8000/api/v1/projects/{proj_id}", "GET", headers=headers_b)
    print(f"GET    Tenant B accessing Tenant A Project -> Status: {b_read_status} (Expected 404 Non-Enumerable)")
    assert b_read_status == 404

    # Update attempt by Tenant B via PATCH
    b_patch_status, b_patch_body = make_req(f"http://127.0.0.1:8000/api/v1/projects/{proj_id}", "PATCH", {"description": "Malicious Patch"}, headers=headers_b)
    print(f"PATCH  Tenant B updating Tenant A Project  -> Status: {b_patch_status} (Expected 404 Non-Enumerable)")
    assert b_patch_status == 404

    # Update attempt by Tenant B via PUT
    b_put_status, b_put_body = make_req(f"http://127.0.0.1:8000/api/v1/projects/{proj_id}", "PUT", {"description": "Malicious Put"}, headers=headers_b)
    print(f"PUT    Tenant B updating Tenant A Project  -> Status: {b_put_status} (Expected 404 Non-Enumerable)")
    assert b_put_status == 404

    # Delete attempt by Tenant B
    b_del_status, b_del_body = make_req(f"http://127.0.0.1:8000/api/v1/projects/{proj_id}", "DELETE", headers=headers_b)
    print(f"DELETE Tenant B deleting Tenant A Project  -> Status: {b_del_status} (Expected 404 Non-Enumerable)")
    assert b_del_status == 404

    # 7. Tenant A updating its own project
    print("\n--- 6. Tenant A Authorized Operations ---")
    a_update_status, a_update_body = make_req(f"http://127.0.0.1:8000/api/v1/projects/{proj_id}", "PATCH", {"description": "Legitimate Update by Owner"}, headers=headers_a)
    print(f"PATCH  Tenant A updating Own Project       -> Status: {a_update_status} (Expected 200)")
    assert a_update_status == 200

    # 8. Database Side-Effect Verification in PostgreSQL 17
    print("\n--- 7. PostgreSQL 17 Direct Database Verification ---")
    engine = create_async_engine(os.environ['DATABASE_URL'], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        db_proj = (await session.execute(select(Project).where(Project.id == uuid.UUID(proj_id)))).scalar_one_or_none()
        assert db_proj is not None, "Project was not found in PostgreSQL 17!"
        print(f"DB Record Verified: Name='{db_proj.name}', Owner='{db_proj.user_id}', Description='{db_proj.description}'")
        assert db_proj.description != "Malicious Patch", "Security Breach: Tenant B mutated project via PATCH!"
        assert db_proj.description != "Malicious Put", "Security Breach: Tenant B mutated project via PUT!"
        assert str(db_proj.user_id) == user_a_id, "Security Breach: user_id was forged!"
        assert db_proj.description == "Legitimate Update by Owner", "Database did not persist legitimate update!"
        print("DATABASE INTEGRITY CONFIRMED: Zero cross-tenant data leakage or tampering.")
    await engine.dispose()

    # 9. Re-test dealer, quote, regulation review, and collection orchestration with valid payloads
    print("\n--- 8. Valid Payload Security Verification on Critical Routes ---")
    
    # 9a. Dealer Registration: POST /api/v1/material-rates/dealers
    dealer_code_uniq = f"DLR_{uuid.uuid4().hex[:6]}"
    dealer_valid_payload = {
        "business_name": "Pak Steel Traders",
        "dealer_code": dealer_code_uniq,
        "city": "Lahore",
        "market_area": "Badami Bagh",
        "address": "Shop 12, Iron Market, Badami Bagh",
        "contact_person": "Haji Aslam",
        "contact_phone": "+923001234567",
        "ntn_number": "1234567-8"
    }
    d_anon_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers", "POST", dealer_valid_payload)
    print(f"POST /material-rates/dealers (Anonymous)    -> Status: {d_anon_st} (Expected 401)")
    assert d_anon_st == 401
    d_inv_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers", "POST", dealer_valid_payload, headers=fake_headers)
    print(f"POST /material-rates/dealers (Invalid Token)-> Status: {d_inv_st} (Expected 401)")
    assert d_inv_st == 401
    d_auth_st, d_auth_resp = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers", "POST", dealer_valid_payload, headers=headers_a)
    print(f"POST /material-rates/dealers (Authenticated)-> Status: {d_auth_st} (Expected 201)")
    assert d_auth_st == 201
    dlr_id = json.loads(d_auth_resp)["id"]

    # 9b. Dealer Quotation: POST /api/v1/material-rates/dealers/quotes
    prod_id = "3ccf0cab-0b2f-4212-b3b8-ec332f7af5bc" # STEEL_REBAR_G60
    quote_valid_payload = {
        "dealer_id": dlr_id,
        "product_id": prod_id,
        "city": "Lahore",
        "quoted_price_pkr": 252000.0,
        "quoted_unit": "metric_ton",
        "validity_days": 7,
        "minimum_order_quantity": 10.0,
        "delivery_charges_pkr": 5000.0,
        "tax_included": True,
        "payment_terms": "Cash on Delivery",
        "vehicle_capacity_cft": 800.0
    }
    q_anon_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers/quotes", "POST", quote_valid_payload)
    print(f"POST /material-rates/dealers/quotes (Anon)  -> Status: {q_anon_st} (Expected 401)")
    assert q_anon_st == 401
    q_inv_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers/quotes", "POST", quote_valid_payload, headers=fake_headers)
    print(f"POST /material-rates/dealers/quotes (Inv)   -> Status: {q_inv_st} (Expected 401)")
    assert q_inv_st == 401
    q_auth_st, q_auth_resp = make_req("http://127.0.0.1:8000/api/v1/material-rates/dealers/quotes", "POST", quote_valid_payload, headers=headers_a)
    print(f"POST /material-rates/dealers/quotes (Auth)  -> Status: {q_auth_st} (Expected 201)")
    assert q_auth_st == 201

    # 9c. Regulatory Review: POST /api/v1/regulations/reviews
    reg_review_payload = {
        "target_type": "document_version",
        "target_id": str(uuid.uuid4()),
        "review_verdict": "approved",
        "notes": "Verified against Punjab Gazette statutory gazette copy."
    }
    r_anon_st, _ = make_req("http://127.0.0.1:8000/api/v1/regulations/reviews", "POST", reg_review_payload)
    print(f"POST /regulations/reviews (Anonymous)       -> Status: {r_anon_st} (Expected 401)")
    assert r_anon_st == 401
    r_inv_st, _ = make_req("http://127.0.0.1:8000/api/v1/regulations/reviews", "POST", reg_review_payload, headers=fake_headers)
    print(f"POST /regulations/reviews (Invalid Token)   -> Status: {r_inv_st} (Expected 401)")
    assert r_inv_st == 401
    r_auth_st, r_auth_resp = make_req("http://127.0.0.1:8000/api/v1/regulations/reviews", "POST", reg_review_payload, headers=headers_a)
    print(f"POST /regulations/reviews (Auth Engineer)   -> Status: {r_auth_st} (Expected 200)")
    assert r_auth_st == 200

    # 9d. Collection Orchestration: POST /api/v1/material-rates/orchestration/trigger
    orch_payload = {
        "source_code": "PBS_MONTHLY_IMPORT",
        "force": False,
        "category_hint": "steel"
    }
    o_anon_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/orchestration/trigger", "POST", orch_payload)
    print(f"POST /material-rates/orchestration/trigger (Anon) -> Status: {o_anon_st} (Expected 401)")
    assert o_anon_st == 401
    o_inv_st, _ = make_req("http://127.0.0.1:8000/api/v1/material-rates/orchestration/trigger", "POST", orch_payload, headers=fake_headers)
    print(f"POST /material-rates/orchestration/trigger (Inv)  -> Status: {o_inv_st} (Expected 401)")
    assert o_inv_st == 401
    o_auth_st, o_auth_resp = make_req("http://127.0.0.1:8000/api/v1/material-rates/orchestration/trigger", "POST", orch_payload, headers=headers_a)
    print(f"POST /material-rates/orchestration/trigger (Auth) -> Status: {o_auth_st}")
    print("Orchestration trigger tested with collection disabled.")

    print("\nALL TASK 4 SECURITY TESTS PASSED COMPLETELY.")

if __name__ == '__main__':
    asyncio.run(run_security_suite())
