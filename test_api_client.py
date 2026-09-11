#!/usr/bin/env python3
"""
Phase 5 API Test Client
=======================

Simple client script to test all Phase 5 API endpoints.

Usage:
    python test_api_client.py
    python test_api_client.py --customer-id C000005
    python test_api_client.py --endpoint churn
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
HEALTH_URL = "http://localhost:5000/health"
API_KEY = "test-key"  # Change this to your actual API key

# Headers
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def check_health() -> bool:
    """Check if API server is running"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API Server is healthy (Models loaded: {data.get('models_loaded')})")
            return True
        else:
            print_error(f"API Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API Server at {HEALTH_URL}")
        print_info("Make sure the API server is running: python phase5_api_server.py")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_churn_prediction(customer_id: str) -> bool:
    """Test churn prediction endpoint"""
    print_header(f"Testing Churn Prediction for {customer_id}")
    
    url = f"{API_BASE_URL}/predict/churn"
    payload = {"customer_id": customer_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Churn prediction successful")
            print(f"  Churn Probability: {data['churn_probability']:.4f}")
            print(f"  Churn Prediction: {data['churn_prediction']}")
            print(f"  Risk Level: {data['risk_level']}")
            print(f"  Model Version: {data['model_version']}")
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Churn prediction test failed: {e}")
        return False

def test_revenue_prediction(customer_id: str) -> bool:
    """Test revenue prediction endpoint"""
    print_header(f"Testing Revenue Prediction for {customer_id}")
    
    url = f"{API_BASE_URL}/predict/revenue"
    payload = {"customer_id": customer_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Revenue prediction successful")
            print(f"  Revenue Forecast: ${data['revenue_forecast']:.2f}")
            print(f"  Revenue Bracket: {data['revenue_bracket']}")
            print(f"  Model Version: {data['model_version']}")
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Revenue prediction test failed: {e}")
        return False

def test_engagement_prediction(customer_id: str) -> bool:
    """Test engagement prediction endpoint"""
    print_header(f"Testing Engagement Prediction for {customer_id}")
    
    url = f"{API_BASE_URL}/predict/engagement"
    payload = {"customer_id": customer_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Engagement prediction successful")
            print(f"  Engagement Score: {data['engagement_score']:.2f}/100")
            print(f"  Engagement Level: {data['engagement_level']}")
            print(f"  Model Version: {data['model_version']}")
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Engagement prediction test failed: {e}")
        return False

def test_segment_prediction(customer_id: str) -> bool:
    """Test segmentation prediction endpoint"""
    print_header(f"Testing Segmentation for {customer_id}")
    
    url = f"{API_BASE_URL}/predict/segment"
    payload = {"customer_id": customer_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Segmentation successful")
            print(f"  Cluster: {data['cluster']}")
            print(f"  Segment Name: {data['segment_name']}")
            print(f"  Description: {data['description']}")
            print(f"  Model Version: {data['model_version']}")
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Segmentation test failed: {e}")
        return False

def test_batch_prediction(customer_id: str) -> bool:
    """Test batch prediction endpoint"""
    print_header(f"Testing Batch Prediction for {customer_id}")
    
    url = f"{API_BASE_URL}/predict/batch"
    payload = {"customer_id": customer_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Batch prediction successful")
            
            # Churn
            churn = data.get('churn', {})
            print(f"  Churn Risk: {churn.get('risk_level')} ({churn.get('churn_probability', 0):.4f})")
            
            # Revenue
            revenue = data.get('revenue', {})
            print(f"  Revenue Forecast: ${revenue.get('revenue_forecast', 0):.2f}")
            
            # Engagement
            engagement = data.get('engagement', {})
            print(f"  Engagement Score: {engagement.get('engagement_level')} ({engagement.get('engagement_score', 0):.2f})")
            
            # Segment
            segment = data.get('segment', {})
            print(f"  Customer Segment: {segment.get('segment_name')}")
            
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Batch prediction test failed: {e}")
        return False

def test_model_status() -> bool:
    """Test model status endpoint"""
    print_header("Testing Model Status")
    
    url = f"{API_BASE_URL}/models/status"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Model status retrieved")
            print(f"  Models Loaded: {data['models_loaded']}")
            print(f"  Models: {', '.join(data['models'])}")
            print(f"  Scalers: {', '.join(data['scalers'])}")
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Model status test failed: {e}")
        return False

def test_error_handling() -> bool:
    """Test error handling"""
    print_header("Testing Error Handling")
    
    # Test 1: Missing customer_id
    print_info("Test 1: Missing customer_id")
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/churn",
            headers=HEADERS,
            json={},
            timeout=5
        )
        if response.status_code == 400:
            print_success("Correctly returned 400 for missing customer_id")
        else:
            print_error(f"Expected 400, got {response.status_code}")
    except Exception as e:
        print_error(f"Test failed: {e}")
    
    # Test 2: Invalid customer
    print_info("Test 2: Invalid customer")
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/churn",
            headers=HEADERS,
            json={"customer_id": "INVALID_999"},
            timeout=5
        )
        if response.status_code == 404:
            print_success("Correctly returned 404 for invalid customer")
        else:
            print_error(f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_error(f"Test failed: {e}")
    
    # Test 3: Missing API key
    print_info("Test 3: Missing API key")
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/churn",
            headers={"Content-Type": "application/json"},
            json={"customer_id": "C000001"},
            timeout=5
        )
        if response.status_code == 401:
            print_success("Correctly returned 401 for missing API key")
        else:
            print_error(f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_error(f"Test failed: {e}")
    
    return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Test Phase 5 API endpoints')
    parser.add_argument('--customer-id', default='C000001', help='Customer ID to test')
    parser.add_argument('--endpoint', help='Specific endpoint to test (churn, revenue, engagement, segment, batch, status)')
    parser.add_argument('--test-errors', action='store_true', help='Test error handling')
    args = parser.parse_args()
    
    print_header("PHASE 5: API TEST CLIENT")
    print_info(f"Base URL: {API_BASE_URL}")
    print_info(f"Customer ID: {args.customer_id}\n")
    
    # Step 1: Check health
    if not check_health():
        print_error("API Server is not responding. Please start it first.")
        return False
    
    # Step 2: Run tests
    results = {}
    
    if args.endpoint == 'churn' or not args.endpoint:
        results['churn'] = test_churn_prediction(args.customer_id)
    
    if args.endpoint == 'revenue' or not args.endpoint:
        results['revenue'] = test_revenue_prediction(args.customer_id)
    
    if args.endpoint == 'engagement' or not args.endpoint:
        results['engagement'] = test_engagement_prediction(args.customer_id)
    
    if args.endpoint == 'segment' or not args.endpoint:
        results['segment'] = test_segment_prediction(args.customer_id)
    
    if args.endpoint == 'batch' or not args.endpoint:
        results['batch'] = test_batch_prediction(args.customer_id)
    
    if args.endpoint == 'status' or not args.endpoint:
        results['status'] = test_model_status()
    
    if args.test_errors:
        results['error_handling'] = test_error_handling()
    
    # Step 3: Summary
    print_header("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name.upper():20s} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
