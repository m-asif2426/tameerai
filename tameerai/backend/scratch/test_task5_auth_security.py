"""
TASK 5 — AUTHENTICATION FINAL SECURITY VERIFICATION
Tests:
1. Set-Cookie attributes on Login (HttpOnly, SameSite, Path)
2. Refresh token rotation (Fresh access token + New Set-Cookie)
3. Replay attack detection (Re-use of old rotated token triggers 401 and revokes all sessions)
4. Logout revocation & cookie clearance
5. Refresh attempt after logout (Rejected 401)
6. Masking of all sensitive credentials/tokens in output
"""

import urllib.request
import urllib.error
import json
import uuid
import re

BASE_URL = "http://127.0.0.1:8000/api/v1"

def parse_cookie_header(header_value):
    """Parses Set-Cookie header into name, masked_val, attributes dict."""
    parts = [p.strip() for p in header_value.split(";")]
    name_val = parts[0].split("=", 1)
    name = name_val[0]
    val = name_val[1] if len(name_val) > 1 else ""
    attrs = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            attrs[k.lower()] = v
        else:
            attrs[p.lower()] = True
    return name, val, attrs

def run_task5_verification():
    print("="*60)
    print("TASK 5 — AUTHENTICATION SECURITY VERIFICATION")
    print("="*60)

    # 1. Register a test user
    email = f"task5_audit_{uuid.uuid4().hex[:6]}@tameerai.pk"
    pwd = "SecuredPassword99#!"
    
    reg_req = urllib.request.Request(
        f"{BASE_URL}/auth/register",
        data=json.dumps({
            "email": email,
            "password": pwd,
            "full_name": "Task5 Security Auditor",
            "role": "engineer"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(reg_req) as resp:
        assert resp.status == 201

    # 2. Login and inspect Set-Cookie
    login_req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=json.dumps({"email": email, "password": pwd}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as resp:
        assert resp.status == 200
        set_cookie = resp.headers.get("Set-Cookie")
        body = json.loads(resp.read().decode("utf-8"))
        
    assert set_cookie is not None, "Missing Set-Cookie header on login"
    cookie_name, raw_cookie_val, cookie_attrs = parse_cookie_header(set_cookie)
    
    # Assert security attributes
    assert "httponly" in cookie_attrs, "HttpOnly flag missing!"
    assert "path" in cookie_attrs and cookie_attrs["path"] == "/api/v1/auth", f"Path not scoped to /api/v1/auth: {cookie_attrs.get('path')}"
    assert "samesite" in cookie_attrs, "SameSite flag missing!"
    
    print(f"[PASS] 1. Set-Cookie verified on Login:")
    print(f"       Name: {cookie_name}")
    print(f"       Value: [PROTECTED / MASKED — {len(raw_cookie_val)} chars]")
    print(f"       HttpOnly: {cookie_attrs.get('httponly')}")
    print(f"       SameSite: {cookie_attrs.get('samesite')}")
    print(f"       Path: {cookie_attrs.get('path')}")
    print(f"       Secure: {cookie_attrs.get('secure', False)} (False in local development / True in production)")

    # 3. Refresh Token Rotation
    refresh_req = urllib.request.Request(
        f"{BASE_URL}/auth/refresh",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"{cookie_name}={raw_cookie_val}"
        }
    )
    with urllib.request.urlopen(refresh_req) as resp:
        assert resp.status == 200
        rotated_set_cookie = resp.headers.get("Set-Cookie")
        refresh_body = json.loads(resp.read().decode("utf-8"))
        
    assert rotated_set_cookie is not None, "Missing Set-Cookie header on rotation"
    _, rotated_cookie_val, rotated_attrs = parse_cookie_header(rotated_set_cookie)
    assert rotated_cookie_val != raw_cookie_val, "Refresh token was not rotated!"
    assert refresh_body.get("accessToken") is not None, "Did not receive new accessToken"
    
    print(f"[PASS] 2. Refresh Token Rotation verified:")
    print(f"       Old Token: [MASKED — {len(raw_cookie_val)} chars]")
    print(f"       Rotated Token: [MASKED — {len(rotated_cookie_val)} chars]")
    print(f"       Fresh Access Token: Issued successfully")
    print(f"       Tokens are distinct: True")

    # 4. Replay Attack Detection (Attempt to reuse old token)
    replay_req = urllib.request.Request(
        f"{BASE_URL}/auth/refresh",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"{cookie_name}={raw_cookie_val}"
        }
    )
    try:
        with urllib.request.urlopen(replay_req) as resp:
            assert False, "Expected 401 on token replay, got 200"
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
        err_msg = json.loads(e.read().decode("utf-8"))
        print(f"[PASS] 3. Replay Attack Detection verified:")
        print(f"       Status: HTTP {e.code}")
        print(f"       Detail: {err_msg.get('detail')}")

    # 5. Verify all sessions were revoked as a result of replay detection
    check_rotated_req = urllib.request.Request(
        f"{BASE_URL}/auth/refresh",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"{cookie_name}={rotated_cookie_val}"
        }
    )
    try:
        with urllib.request.urlopen(check_rotated_req) as resp:
            assert False, "Expected 401 because all sessions should be revoked after replay attack"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] 4. Replay Containment verified: All sessions revoked upon replay attempt.")

    # 6. Test Clean Logout & Post-Logout Refresh
    # Login again to establish clean session
    login2_req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=json.dumps({"email": email, "password": pwd}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login2_req) as resp:
        fresh_set_cookie = resp.headers.get("Set-Cookie")
        _, fresh_cookie_val, _ = parse_cookie_header(fresh_set_cookie)

    # Logout
    logout_req = urllib.request.Request(
        f"{BASE_URL}/auth/logout",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"{cookie_name}={fresh_cookie_val}"
        }
    )
    with urllib.request.urlopen(logout_req) as resp:
        assert resp.status == 200
        logout_cookie = resp.headers.get("Set-Cookie")
        logout_body = json.loads(resp.read().decode("utf-8"))
        
    _, cleared_val, logout_attrs = parse_cookie_header(logout_cookie)
    assert cleared_val == '""' or cleared_val == "" or "max-age" in logout_attrs, "Cookie not cleared on logout"
    print(f"[PASS] 5. Logout Revocation verified:")
    print(f"       Logout message: {logout_body.get('message')}")
    print(f"       Cleared Cookie Set-Cookie: {logout_cookie}")

    # Refresh attempt after logout must fail
    post_logout_refresh = urllib.request.Request(
        f"{BASE_URL}/auth/refresh",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"{cookie_name}={fresh_cookie_val}"
        }
    )
    try:
        with urllib.request.urlopen(post_logout_refresh) as resp:
            assert False, "Expected 401 on refresh after logout"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] 6. Refresh after logout rejected: HTTP {e.code}")

    print("="*60)
    print("TASK 5 EVIDENCE COLLECTION: 100% PASS")
    print("="*60)

if __name__ == "__main__":
    run_task5_verification()

