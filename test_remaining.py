#!/usr/bin/env python3
"""Quick test for segmentation endpoint"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "customer_id": "C000001"
}

print("Testing /api/v1/predict/segment endpoint...")
print(f"Payload: {payload}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/predict/segment",
        json=payload,
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("Testing /api/v1/predict/batch endpoint...")

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
    result = response.json()
    print(f"Predictions count: {len(result.get('predictions', []))}")
    if result.get('predictions'):
        print(f"First prediction: {json.dumps(result['predictions'][0], indent=2)}")
except Exception as e:
    print(f"Error: {e}")
