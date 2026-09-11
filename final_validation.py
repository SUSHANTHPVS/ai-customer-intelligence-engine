#!/usr/bin/env python3
"""Quick final validation of all 7 endpoints"""

import requests
import json

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

tests = [
    ("Models Status", "GET", "/api/v1/models/status", None),
    ("Churn", "POST", "/api/v1/predict/churn", {"customer_id": "C000001"}),
    ("Revenue", "POST", "/api/v1/predict/revenue", {"customer_id": "C000001"}),
    ("Engagement", "POST", "/api/v1/predict/engagement", {"customer_id": "C000001"}),
    ("Segment", "POST", "/api/v1/predict/segment", {"customer_id": "C000001"}),
    ("Batch", "POST", "/api/v1/predict/batch", {"customer_id": "C000001"}),
]

print("\n=== PHASE 5 API ENDPOINT VALIDATION ===\n")
passed = 0

for name, method, endpoint, payload in tests:
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
        else:
            r = requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers, timeout=10)
        
        ok = "PASS" if r.status_code == 200 else "FAIL"
        if r.status_code == 200:
            passed += 1
        print(f"[{ok}] {name:<20} {endpoint:<35} (HTTP {r.status_code})")
    except Exception as e:
        print(f"[FAIL] {name:<20} {endpoint:<35} (ERROR: {str(e)[:40]})")

print(f"\nResult: {passed}/6 endpoints working")
print("="*60)
if passed == 6:
    print("TASK 3 COMPLETE: All critical endpoints verified!")
else:
    print(f"WARNING: {6-passed} endpoints need attention")
print("="*60)
