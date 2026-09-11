#!/usr/bin/env python3
"""
Load Testing Suite for AI Customer Intelligence API
Tests API performance under concurrent load
"""

import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
from typing import List, Dict

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = "test-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.results = []
        self.errors = []
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def test_single_request(self, endpoint: str, customer_id: str = "C000001") -> Dict:
        """Test a single request and return metrics"""
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json={"customer_id": customer_id},
                timeout=10
            )
            elapsed = time.time() - start_time
            
            return {
                'endpoint': endpoint,
                'customer_id': customer_id,
                'status_code': response.status_code,
                'response_time_ms': elapsed * 1000,
                'success': 200 <= response.status_code < 300,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'endpoint': endpoint,
                'customer_id': customer_id,
                'error': str(e),
                'response_time_ms': elapsed * 1000,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def load_test_endpoint(self, endpoint: str, num_requests: int = 100, 
                           num_workers: int = 10, customer_ids: List[str] = None) -> Dict:
        """Test endpoint with concurrent load"""
        if customer_ids is None:
            customer_ids = [f"C{i:06d}" for i in range(1, 11)]  # Default: C000001 to C000010
        
        print(f"\n{Colors.HEADER}{'='*60}")
        print(f"LOAD TEST: {endpoint}")
        print(f"{'='*60}{Colors.ENDC}")
        print(f"Requests: {num_requests} | Workers: {num_workers} | Time: {datetime.now().strftime('%H:%M:%S')}")
        
        response_times = []
        request_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for i in range(num_requests):
                customer_id = customer_ids[i % len(customer_ids)]
                futures.append(executor.submit(self.test_single_request, endpoint, customer_id))
            
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                
                if result['success']:
                    response_times.append(result['response_time_ms'])
                    print(f"{Colors.OKGREEN}✓{Colors.ENDC}", end="", flush=True)
                    request_count += 1
                else:
                    error_count += 1
                    print(f"{Colors.FAIL}✗{Colors.ENDC}", end="", flush=True)
                    self.errors.append(result)
        
        print()  # New line after progress dots
        
        # Calculate statistics
        if response_times:
            stats = {
                'endpoint': endpoint,
                'total_requests': num_requests,
                'successful_requests': request_count,
                'failed_requests': error_count,
                'success_rate': (request_count / num_requests) * 100,
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'avg_response_time_ms': statistics.mean(response_times),
                'median_response_time_ms': statistics.median(response_times),
                'std_dev_response_time_ms': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'p95_response_time_ms': sorted(response_times)[int(len(response_times) * 0.95)],
                'p99_response_time_ms': sorted(response_times)[int(len(response_times) * 0.99)],
                'requests_per_second': num_requests / (sum(response_times) / 1000 / num_requests)
            }
        else:
            stats = {
                'endpoint': endpoint,
                'total_requests': num_requests,
                'successful_requests': 0,
                'failed_requests': error_count,
                'success_rate': 0,
                'error': 'All requests failed'
            }
        
        self._print_stats(stats)
        return stats
    
    def _print_stats(self, stats: Dict):
        """Print formatted statistics"""
        print(f"\n{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
        print(f"  Total Requests:    {stats.get('total_requests', 0)}")
        print(f"  Successful:        {Colors.OKGREEN}{stats.get('successful_requests', 0)}{Colors.ENDC}")
        print(f"  Failed:            {Colors.FAIL}{stats.get('failed_requests', 0)}{Colors.ENDC}")
        print(f"  Success Rate:      {Colors.OKBLUE}{stats.get('success_rate', 0):.1f}%{Colors.ENDC}")
        
        if 'avg_response_time_ms' in stats:
            print(f"\n{Colors.BOLD}Response Times (ms):{Colors.ENDC}")
            print(f"  Min:               {stats['min_response_time_ms']:.2f}ms")
            print(f"  Max:               {stats['max_response_time_ms']:.2f}ms")
            print(f"  Average:           {stats['avg_response_time_ms']:.2f}ms")
            print(f"  Median:            {stats['median_response_time_ms']:.2f}ms")
            print(f"  Std Dev:           {stats['std_dev_response_time_ms']:.2f}ms")
            print(f"  P95:               {stats['p95_response_time_ms']:.2f}ms")
            print(f"  P99:               {stats['p99_response_time_ms']:.2f}ms")
            print(f"  RPS:               {stats['requests_per_second']:.2f}")
    
    def run_full_load_test(self, num_requests: int = 100, num_workers: int = 10):
        """Run load test on all endpoints"""
        endpoints = [
            '/api/v1/predict/churn',
            '/api/v1/predict/revenue',
            '/api/v1/predict/engagement',
            '/api/v1/predict/segment',
            '/api/v1/predict/batch'
        ]
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════╗")
        print("║    AI CUSTOMER INTELLIGENCE - LOAD TESTING SUITE       ║")
        print("╚════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        all_stats = []
        for endpoint in endpoints:
            stats = self.load_test_endpoint(endpoint, num_requests, num_workers)
            all_stats.append(stats)
        
        self._print_summary(all_stats)
        self._save_results(all_stats)
    
    def _print_summary(self, all_stats: List[Dict]):
        """Print overall summary"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("═" * 60)
        print("LOAD TEST SUMMARY")
        print("═" * 60)
        print(f"{Colors.ENDC}")
        
        total_requests = sum(s.get('total_requests', 0) for s in all_stats)
        total_successful = sum(s.get('successful_requests', 0) for s in all_stats)
        total_failed = sum(s.get('failed_requests', 0) for s in all_stats)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"Overall Success Rate: {Colors.OKGREEN if overall_success_rate > 95 else Colors.WARNING}{overall_success_rate:.1f}%{Colors.ENDC}")
        print(f"Total Requests:       {total_requests}")
        print(f"Successful:           {Colors.OKGREEN}{total_successful}{Colors.ENDC}")
        print(f"Failed:               {Colors.FAIL}{total_failed}{Colors.ENDC}")
        
        if total_successful > 0:
            avg_times = [s.get('avg_response_time_ms', 0) for s in all_stats]
            print(f"\nAverage Response Times (ms):")
            for stat in all_stats:
                print(f"  {stat['endpoint']:30s} {stat.get('avg_response_time_ms', 0):8.2f}ms")
    
    def _save_results(self, all_stats: List[Dict]):
        """Save results to JSON file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': all_stats,
            'detailed_results': self.results,
            'errors': self.errors
        }
        
        filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n{Colors.OKGREEN}✓{Colors.ENDC} Results saved to: {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Load Testing Suite for AI Customer Intelligence API')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of API (default: http://localhost:5000)')
    parser.add_argument('--requests', '-r', type=int, default=100, help='Number of requests per endpoint (default: 100)')
    parser.add_argument('--workers', '-w', type=int, default=10, help='Number of concurrent workers (default: 10)')
    parser.add_argument('--api-key', default='test-key', help='API key for authentication (default: test-key)')
    
    args = parser.parse_args()
    
    tester = LoadTester(base_url=args.url, api_key=args.api_key)
    tester.run_full_load_test(num_requests=args.requests, num_workers=args.workers)

if __name__ == '__main__':
    main()
