#!/usr/bin/env python3
"""
PHASE 5 API - COMPREHENSIVE TEST REPORT
Tests all 7 REST endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Test results tracking
results = []

def test_endpoint(name, method, endpoint, payload=None):
    """Test an endpoint and record results"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        success = response.status_code == 200
        results.append({
            'name': name,
            'endpoint': endpoint,
            'status': response.status_code,
            'success': success,
            'response': response.json() if response.text else {}
        })
        return success
    except Exception as e:
        results.append({
            'name': name,
            'endpoint': endpoint,
            'status': 'ERROR',
            'success': False,
            'error': str(e)
        })
        return False

print("="*70)
print("PHASE 5 API - COMPREHENSIVE TEST REPORT")
print("="*70)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Test 1: Health check
print("[1/7] Testing GET /health")
test_endpoint("Health Check", "GET", "/health")

# Test 2: Models status
print("[2/7] Testing GET /api/v1/models/status")
test_endpoint("Models Status", "GET", "/api/v1/models/status")

# Test 3: Churn prediction
print("[3/7] Testing POST /api/v1/predict/churn")
test_endpoint("Churn Prediction", "POST", "/api/v1/predict/churn", 
              {"customer_id": "C000001"})

# Test 4: Revenue prediction
print("[4/7] Testing POST /api/v1/predict/revenue")
test_endpoint("Revenue Forecast", "POST", "/api/v1/predict/revenue",
              {"customer_id": "C000001"})

# Test 5: Engagement prediction
print("[5/7] Testing POST /api/v1/predict/engagement")
test_endpoint("Engagement Score", "POST", "/api/v1/predict/engagement",
              {"customer_id": "C000001"})

# Test 6: Segmentation
print("[6/7] Testing POST /api/v1/predict/segment")
test_endpoint("Customer Segmentation", "POST", "/api/v1/predict/segment",
              {"customer_id": "C000001"})

# Test 7: Batch predictions
print("[7/7] Testing POST /api/v1/predict/batch")
test_endpoint("Batch Predictions", "POST", "/api/v1/predict/batch",
              {"customer_id": "C000001"})

# Print summary
print("\n" + "="*70)
print("TEST RESULTS SUMMARY")
print("="*70)

passed = sum(1 for r in results if r['success'])
total = len(results)

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {total - passed}")
print(f"Success Rate: {(passed/total)*100:.1f}%\n")

for i, result in enumerate(results, 1):
    status = "[PASS]" if result['success'] else "[FAIL]"
    http_code = result.get('status', 'ERROR')
    print(f"{i}. {status} {result['name']:<30} (HTTP {http_code}) - {result['endpoint']}")

print("\n" + "="*70)
print("ENDPOINT DETAILS")
print("="*70 + "\n")

for result in results:
    if result['success']:
        print(f"[PASS] {result['name']}")
        print(f"       Endpoint: {result['endpoint']}")
        print(f"       Status: {result['status']}")
        if 'churn' in result['response']:
            print(f"       Churn Probability: {result['response'].get('churn_probability', 'N/A')}")
        if 'revenue_forecast' in result['response']:
            print(f"       Revenue Forecast: ${result['response'].get('revenue_forecast', 'N/A')}")
        if 'engagement_score' in result['response']:
            print(f"       Engagement Score: {result['response'].get('engagement_score', 'N/A')}")
        if 'segment_name' in result['response']:
            print(f"       Customer Segment: {result['response'].get('segment_name', 'N/A')}")
        print()

print("="*70)
print("CONCLUSION")
print("="*70)
if passed == total:
    print("\nALL ENDPOINTS WORKING SUCCESSFULLY!")
    print("Task 3: Run test suite for all endpoints - COMPLETED")
else:
    print(f"\n{total - passed} endpoint(s) need attention")
print("="*70)
