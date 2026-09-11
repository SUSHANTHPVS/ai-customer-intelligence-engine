#!/usr/bin/env python3
"""Test batch endpoint and show error"""

import requests
import json

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

batch_payload = {
    "customer_ids": ["C000001", "C000002", "C000003"]
}
print(f"Payload: {batch_payload}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/predict/batch",
        json=batch_payload,
        headers=headers,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Full Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
