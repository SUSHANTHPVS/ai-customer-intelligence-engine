#!/usr/bin/env python3
"""Quick Load Test - Phase 5 API Performance"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import statistics

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def test_request(endpoint, customer_id):
    """Single request test"""
    try:
        start = time.time()
        r = requests.post(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            json={"customer_id": customer_id},
            timeout=10
        )
        elapsed = (time.time() - start) * 1000
        return {
            'success': r.status_code == 200,
            'time_ms': elapsed,
            'status': r.status_code
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'time_ms': 0}

def load_test(endpoint, num_requests=50, num_workers=5):
    """Run load test"""
    print(f"\nTesting {endpoint} with {num_requests} requests ({num_workers} workers)...")
    
    results = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_requests):
            cid = f"C{i%10:06d}"
            futures.append(executor.submit(test_request, endpoint, cid))
        
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            status = "✓" if result['success'] else "✗"
            print(f"{status}", end="", flush=True)
            if (i + 1) % 10 == 0:
                print(f" ({i+1}/{num_requests})", flush=True)
    
    # Calculate statistics
    successful = [r['time_ms'] for r in results if r['success']]
    total_reqs = len(results)
    success_count = len(successful)
    
    if successful:
        avg_time = statistics.mean(successful)
        min_time = min(successful)
        max_time = max(successful)
        median_time = statistics.median(successful)
        
        # Percentiles
        sorted_times = sorted(successful)
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
        
        print(f"\n  Success Rate: {success_count}/{total_reqs} ({(success_count/total_reqs)*100:.1f}%)")
        print(f"  Response Times:")
        print(f"    Min:    {min_time:.2f}ms")
        print(f"    Max:    {max_time:.2f}ms")
        print(f"    Avg:    {avg_time:.2f}ms")
        print(f"    Median: {median_time:.2f}ms")
        print(f"    P95:    {p95:.2f}ms")
        print(f"    P99:    {p99:.2f}ms")
        
        # RPS calculation
        total_time = sum(successful) / 1000
        rps = len(successful) / total_time if total_time > 0 else 0
        print(f"  Throughput: {rps:.2f} req/s")
        
        return {
            'endpoint': endpoint,
            'requests': total_reqs,
            'success': success_count,
            'success_rate': (success_count/total_reqs)*100,
            'avg_response_time': avg_time,
            'p95_response_time': p95,
            'p99_response_time': p99,
            'throughput_rps': rps
        }
    else:
        print(f"\n  ERROR: All {total_reqs} requests failed!")
        return None

# Run tests
print("="*60)
print("PHASE 5 API - LOAD TEST")
print("="*60)
print(f"Start Time: {datetime.now().isoformat()}")
print(f"API: {BASE_URL}")

results = {}

# Test each endpoint
endpoints = [
    '/api/v1/predict/churn',
    '/api/v1/predict/revenue',
    '/api/v1/predict/engagement',
    '/api/v1/predict/segment',
]

for endpoint in endpoints:
    result = load_test(endpoint, num_requests=50, num_workers=5)
    if result:
        results[endpoint] = result

# Summary
print("\n" + "="*60)
print("LOAD TEST SUMMARY")
print("="*60)

total_requests = sum(r['requests'] for r in results.values())
total_success = sum(r['success'] for r in results.values())

for endpoint, data in results.items():
    print(f"\n{endpoint}:")
    print(f"  Success Rate: {data['success_rate']:.1f}%")
    print(f"  Avg Response: {data['avg_response_time']:.2f}ms")
    print(f"  P95 Response: {data['p95_response_time']:.2f}ms")
    print(f"  Throughput:  {data['throughput_rps']:.2f} req/s")

print(f"\nOVERALL:")
print(f"  Total Requests: {total_requests}")
print(f"  Successful: {total_success}/{total_requests} ({(total_success/total_requests)*100:.1f}%)")
print(f"  End Time: {datetime.now().isoformat()}")
print("="*60)

if (total_success/total_requests)*100 >= 95:
    print("LOAD TEST PASSED: API performs well under load!")
else:
    print("LOAD TEST WARNING: Success rate below 95%")
print("="*60)
