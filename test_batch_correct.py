#!/usr/bin/env python3
"""Test batch endpoint with correct payload"""

import requests
import json

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Batch endpoint expects single customer_id and returns all 4 predictions
batch_payload = {
    "customer_id": "C000001"
}
print(f"Testing /api/v1/predict/batch with payload: {batch_payload}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/predict/batch",
        json=batch_payload,
        headers=headers,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Full Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
