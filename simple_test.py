#!/usr/bin/env python3
"""Simple API test without unicode characters"""

import requests
import json

API_BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "test-key"

def test_endpoint(method, endpoint, data=None):
    """Test an endpoint"""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5)
        else:
            resp = requests.post(url, headers=headers, json=data, timeout=5)
        
        print(f"\n{endpoint}:")
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"  Result: {json.dumps(result, indent=4)}")
            return True
        else:
            print(f"  Error: {resp.json()}")
            return False
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return False

# Test endpoints
print("\n=== PHASE 5 API TEST ===\n")

customer_id = "C000001"

# Health check
test_endpoint("GET", "health")

# Status
test_endpoint("GET", "models/status")

# Churn prediction
test_endpoint("POST", "predict/churn", {"customer_id": customer_id})

# Revenue prediction
test_endpoint("POST", "predict/revenue", {"customer_id": customer_id})

# Engagement prediction
test_endpoint("POST", "predict/engagement", {"customer_id": customer_id})

# Segmentation
test_endpoint("POST", "predict/segment", {"customer_id": customer_id})

# Batch prediction
test_endpoint("POST", "predict/batch", {"customer_ids": [customer_id]})

print("\n=== TEST COMPLETE ===\n")
