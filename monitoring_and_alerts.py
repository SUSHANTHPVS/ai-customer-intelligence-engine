#!/usr/bin/env python3
"""
Monitoring & Alerting System for AI Customer Intelligence API
Monitors server health, performance metrics, and triggers alerts
"""

import requests
import json
import time
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import threading

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class AlertRule:
    """Define alerting rules"""
    def __init__(self, name: str, condition_func, severity: str = "WARNING"):
        self.name = name
        self.condition_func = condition_func
        self.severity = severity
    
    def check(self, metrics: Dict) -> Tuple[bool, str]:
        """Check if alert condition is met, return (triggered, message)"""
        try:
            result = self.condition_func(metrics)
            return result
        except Exception as e:
            return False, f"Error checking {self.name}: {str(e)}"

class MonitoringSystem:
    def __init__(self, api_url: str = "http://localhost:5000", log_file: str = "api_server.log"):
        self.api_url = api_url
        self.log_file = log_file
        self.api_key = "test-key"
        self.metrics_history = []
        self.alerts = []
        self.setup_alert_rules()
    
    def setup_alert_rules(self):
        """Setup alert rules"""
        self.alert_rules = [
            AlertRule(
                "High Error Rate",
                lambda m: (m.get('error_rate', 0) > 1.0, 
                          f"Error rate {m.get('error_rate', 0):.2f}% exceeds 1% threshold"),
                "CRITICAL"
            ),
            AlertRule(
                "High Latency",
                lambda m: (m.get('avg_latency_ms', 0) > 500,
                          f"Average latency {m.get('avg_latency_ms', 0):.0f}ms exceeds 500ms threshold"),
                "WARNING"
            ),
            AlertRule(
                "Model Load Failure",
                lambda m: (not m.get('models_loaded', True),
                          "One or more ML models failed to load"),
                "CRITICAL"
            ),
            AlertRule(
                "High P95 Latency",
                lambda m: (m.get('p95_latency_ms', 0) > 1000,
                          f"P95 latency {m.get('p95_latency_ms', 0):.0f}ms exceeds 1000ms threshold"),
                "WARNING"
            ),
            AlertRule(
                "Database Connection Error",
                lambda m: (not m.get('db_connected', True),
                          "Database connection failed"),
                "CRITICAL"
            ),
            AlertRule(
                "Memory Usage High",
                lambda m: (m.get('memory_percent', 0) > 80,
                          f"Memory usage {m.get('memory_percent', 0):.1f}% exceeds 80% threshold"),
                "WARNING"
            ),
        ]
    
    def get_api_health(self) -> Dict:
        """Get API health status"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers={'X-API-Key': self.api_key},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'UP',
                    'timestamp': data.get('timestamp'),
                    'models_loaded': len(data.get('loaded_models', [])) > 0,
                    'models_count': len(data.get('loaded_models', []))
                }
        except Exception as e:
            return {'status': 'DOWN', 'error': str(e)}
        return {'status': 'UNKNOWN'}
    
    def parse_log_metrics(self) -> Dict:
        """Parse metrics from API log file"""
        metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'error_rate': 0,
            'latencies': [],
            'avg_latency_ms': 0,
            'p95_latency_ms': 0,
            'errors_last_hour': 0,
            'db_connected': True
        }
        
        if not os.path.exists(self.log_file):
            return metrics
        
        # Read last 1000 lines of log
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-1000:]
            
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            for line in lines:
                # Parse status codes
                if ' - - [' in line and '] "' in line:
                    metrics['total_requests'] += 1
                    
                    # Extract status code
                    match = re.search(r'\] ".*?" (\d{3})', line)
                    if match:
                        status_code = int(match.group(1))
                        if 200 <= status_code < 300:
                            metrics['successful_requests'] += 1
                        else:
                            metrics['failed_requests'] += 1
                    
                    # Extract response time if available
                    match = re.search(r'response_time[_=](\d+\.?\d*)', line)
                    if match:
                        latency = float(match.group(1))
                        metrics['latencies'].append(latency)
                
                # Check for errors
                if 'ERROR' in line or 'EXCEPTION' in line:
                    try:
                        log_time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                        if log_time_match:
                            log_time = datetime.strptime(log_time_match.group(0), '%Y-%m-%d %H:%M:%S')
                            if log_time > one_hour_ago:
                                metrics['errors_last_hour'] += 1
                    except:
                        pass
                
                # Check for DB connection issues
                if 'database' in line.lower() and 'error' in line.lower():
                    metrics['db_connected'] = False
        
        except Exception as e:
            print(f"{Colors.FAIL}Error parsing log: {str(e)}{Colors.ENDC}")
        
        # Calculate derived metrics
        if metrics['total_requests'] > 0:
            metrics['error_rate'] = (metrics['failed_requests'] / metrics['total_requests']) * 100
        
        if metrics['latencies']:
            metrics['avg_latency_ms'] = sum(metrics['latencies']) / len(metrics['latencies']) * 1000
            sorted_latencies = sorted(metrics['latencies'])
            p95_idx = int(len(sorted_latencies) * 0.95)
            metrics['p95_latency_ms'] = sorted_latencies[p95_idx] * 1000 if p95_idx < len(sorted_latencies) else 0
        
        return metrics
    
    def check_alerts(self, health: Dict, metrics: Dict) -> List[Dict]:
        """Check all alert rules"""
        triggered_alerts = []
        
        combined_metrics = {**health, **metrics}
        
        for rule in self.alert_rules:
            triggered, message = rule.check(combined_metrics)
            if triggered:
                triggered_alerts.append({
                    'name': rule.name,
                    'severity': rule.severity,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
        
        return triggered_alerts
    
    def print_dashboard(self, health: Dict, metrics: Dict, alerts: List[Dict]):
        """Print monitoring dashboard"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════╗")
        print("║         MONITORING DASHBOARD - API HEALTH STATUS       ║")
        print("╚════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # API Status
        status_color = Colors.OKGREEN if health.get('status') == 'UP' else Colors.FAIL
        print(f"\n{Colors.BOLD}API Status:{Colors.ENDC}")
        print(f"  Status:            {status_color}{health.get('status')}{Colors.ENDC}")
        print(f"  Models Loaded:     {health.get('models_count', 0)}")
        
        # Request Metrics
        print(f"\n{Colors.BOLD}Request Metrics:{Colors.ENDC}")
        print(f"  Total Requests:    {metrics.get('total_requests', 0)}")
        print(f"  Successful:        {Colors.OKGREEN}{metrics.get('successful_requests', 0)}{Colors.ENDC}")
        print(f"  Failed:            {Colors.FAIL}{metrics.get('failed_requests', 0)}{Colors.ENDC}")
        print(f"  Error Rate:        {Colors.WARNING if metrics.get('error_rate', 0) > 1.0 else Colors.OKGREEN}{metrics.get('error_rate', 0):.2f}%{Colors.ENDC}")
        
        # Performance Metrics
        print(f"\n{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
        print(f"  Avg Latency:       {metrics.get('avg_latency_ms', 0):.2f}ms")
        print(f"  P95 Latency:       {metrics.get('p95_latency_ms', 0):.2f}ms")
        print(f"  Errors (1h):       {metrics.get('errors_last_hour', 0)}")
        
        # Database Status
        db_status = Colors.OKGREEN + "CONNECTED" if metrics.get('db_connected', True) else Colors.FAIL + "DISCONNECTED"
        print(f"\n{Colors.BOLD}Database:{Colors.ENDC}")
        print(f"  Status:            {db_status}{Colors.ENDC}")
        
        # Alerts
        if alerts:
            print(f"\n{Colors.BOLD}{Colors.FAIL}⚠ ALERTS ({len(alerts)}):{Colors.ENDC}")
            for alert in alerts:
                severity_color = Colors.FAIL if alert['severity'] == 'CRITICAL' else Colors.WARNING
                print(f"  {severity_color}[{alert['severity']}] {alert['name']}{Colors.ENDC}")
                print(f"    └─ {alert['message']}")
        else:
            print(f"\n{Colors.OKGREEN}✓ No active alerts{Colors.ENDC}")
    
    def run_monitoring_loop(self, interval: int = 30, duration_minutes: int = None):
        """Run continuous monitoring"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        
        print(f"\n{Colors.OKGREEN}Starting monitoring (interval: {interval}s){Colors.ENDC}")
        if end_time:
            print(f"Will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        iteration = 0
        try:
            while True:
                if end_time and datetime.now() > end_time:
                    break
                
                iteration += 1
                print(f"\n{Colors.OKBLUE}Iteration {iteration}{Colors.ENDC}")
                
                # Collect metrics
                health = self.get_api_health()
                metrics = self.parse_log_metrics()
                alerts = self.check_alerts(health, metrics)
                
                # Store history
                self.metrics_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'health': health,
                    'metrics': metrics,
                    'alerts': alerts
                })
                
                # Print dashboard
                self.print_dashboard(health, metrics, alerts)
                
                # Wait for next interval
                print(f"\nNext check in {interval}s...", end='', flush=True)
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}Monitoring stopped by user{Colors.ENDC}")
        
        self.save_monitoring_report()
    
    def save_monitoring_report(self):
        """Save monitoring report"""
        report = {
            'start_time': self.metrics_history[0]['timestamp'] if self.metrics_history else None,
            'end_time': self.metrics_history[-1]['timestamp'] if self.metrics_history else None,
            'total_iterations': len(self.metrics_history),
            'history': self.metrics_history
        }
        
        filename = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} Report saved to: {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring & Alerts System for AI Customer Intelligence API')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of API')
    parser.add_argument('--log-file', default='api_server.log', help='Path to API log file')
    parser.add_argument('--interval', '-i', type=int, default=30, help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--duration', '-d', type=int, help='Duration to run in minutes (default: infinite)')
    
    args = parser.parse_args()
    
    monitor = MonitoringSystem(api_url=args.url, log_file=args.log_file)
    monitor.run_monitoring_loop(interval=args.interval, duration_minutes=args.duration)

if __name__ == '__main__':
    main()
