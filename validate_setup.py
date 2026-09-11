#!/usr/bin/env python3
"""
AI Customer Intelligence Engine - Tasks A, B, C Validation Script

This script validates the setup of all three tasks:
- Task A: React Dashboard
- Task B: Model Monitoring
- Task C: Prometheus/Grafana

Run this script to verify all systems are working correctly.
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ValidationReport:
    """Generate validation report for all tasks"""
    
    def __init__(self):
        self.checks = []
        self.timestamp = datetime.now().isoformat()
    
    def add_check(self, name, status, message=""):
        """Add a check result"""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message
        })
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n{BLUE}{'='*60}")
        print(f"AI INTELLIGENCE ENGINE - VALIDATION REPORT")
        print(f"{'='*60}{RESET}\n")
        
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c['status'] == 'PASS')
        failed = sum(1 for c in self.checks if c['status'] == 'FAIL')
        warning = sum(1 for c in self.checks if c['status'] == 'WARN')
        
        for check in self.checks:
            if check['status'] == 'PASS':
                icon = f"{GREEN}✓{RESET}"
            elif check['status'] == 'FAIL':
                icon = f"{RED}✗{RESET}"
            else:
                icon = f"{YELLOW}⚠{RESET}"
            
            print(f"{icon} {check['name']}")
            if check['message']:
                print(f"   {check['message']}")
        
        print(f"\n{BLUE}{'-'*60}")
        print(f"Summary: {GREEN}{passed} PASSED{RESET}, {RED}{failed} FAILED{RESET}, {YELLOW}{warning} WARNINGS{RESET}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print(f"{BLUE}{'-'*60}{RESET}\n")
        
        return passed == total

def check_python_packages():
    """Check if required Python packages are installed"""
    print(f"{BLUE}Checking Python packages...{RESET}")
    
    required_packages = {
        'flask': 'Flask',
        'psycopg2': 'psycopg2',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'sklearn': 'scikit-learn',
        'prometheus_client': 'prometheus-client',
    }
    
    report = ValidationReport()
    
    for module, package_name in required_packages.items():
        try:
            __import__(module)
            report.add_check(f"Package: {package_name}", "PASS")
        except ImportError:
            report.add_check(f"Package: {package_name}", "FAIL", 
                           f"Install with: pip install {package_name}")
    
    return report

def check_backend_files():
    """Check if backend files exist"""
    print(f"{BLUE}Checking backend files...{RESET}")
    
    report = ValidationReport()
    backend_path = Path("backend")
    
    required_files = {
        "phase5_api_server.py": "Flask API server",
        "model_monitoring.py": "Model monitoring module",
        "prometheus_exporter.py": "Prometheus metrics exporter",
        "prometheus.yml": "Prometheus configuration",
        "alerting_rules.yml": "Alert rules",
        "alertmanager.yml": "Alertmanager config",
        "grafana_dashboard.json": "Grafana dashboard",
    }
    
    for filename, description in required_files.items():
        filepath = backend_path / filename
        if filepath.exists():
            report.add_check(f"File: {description}", "PASS", str(filepath))
        else:
            report.add_check(f"File: {description}", "FAIL", f"Missing: {filepath}")
    
    return report

def check_frontend_files():
    """Check if frontend files exist"""
    print(f"{BLUE}Checking frontend files...{RESET}")
    
    report = ValidationReport()
    frontend_path = Path("frontend")
    
    required_files = {
        "src/App.jsx": "Main dashboard component",
        "src/components/CustomerSearch.jsx": "Search component",
        "src/components/PredictionDisplay.jsx": "Prediction display",
        "src/components/DashboardCharts.jsx": "Charts component",
        "src/components/ModelMonitoring.jsx": "Monitoring component",
        "vite.config.js": "Vite configuration",
        "tailwind.config.js": "Tailwind configuration",
        "package.json": "Dependencies",
    }
    
    for filename, description in required_files.items():
        filepath = frontend_path / filename
        if filepath.exists():
            report.add_check(f"File: {description}", "PASS", str(filepath))
        else:
            report.add_check(f"File: {description}", "FAIL", f"Missing: {filepath}")
    
    return report

def check_api_server(host='localhost', port=5000):
    """Check if Flask API server is running"""
    print(f"{BLUE}Checking Flask API server (http://{host}:{port})...{RESET}")
    
    report = ValidationReport()
    
    try:
        response = requests.get(f"http://{host}:{port}/api/v1/models/status", 
                               timeout=5, 
                               headers={'X-API-Key': 'test-key'})
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', {})
            report.add_check(f"API Server Status", "PASS", 
                           f"Running with {len(models)} models loaded")
            
            # Check individual models
            for model_name, model_status in models.items():
                status = "PASS" if model_status.get('loaded') else "FAIL"
                report.add_check(f"Model: {model_name}", status)
        else:
            report.add_check(f"API Server Status", "FAIL", 
                           f"Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        report.add_check(f"API Server Status", "FAIL", 
                       f"Cannot connect to http://{host}:{port}")
    except Exception as e:
        report.add_check(f"API Server Status", "FAIL", str(e))
    
    return report

def check_prometheus(host='localhost', port=9090):
    """Check if Prometheus is running"""
    print(f"{BLUE}Checking Prometheus (http://{host}:{port})...{RESET}")
    
    report = ValidationReport()
    
    try:
        response = requests.get(f"http://{host}:{port}/api/v1/status", 
                               timeout=5)
        
        if response.status_code == 200:
            report.add_check(f"Prometheus Status", "PASS", 
                           f"http://{host}:{port}")
            
            # Check targets
            targets_response = requests.get(
                f"http://{host}:{port}/api/v1/targets", 
                timeout=5
            )
            if targets_response.status_code == 200:
                targets = targets_response.json().get('data', {})
                active = targets.get('activeTargets', [])
                report.add_check(f"Prometheus Targets", "PASS", 
                               f"{len(active)} active targets")
        else:
            report.add_check(f"Prometheus Status", "FAIL", 
                           f"Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        report.add_check(f"Prometheus Status", "WARN", 
                       f"Not running on http://{host}:{port} (use docker-compose)")
    except Exception as e:
        report.add_check(f"Prometheus Status", "WARN", str(e))
    
    return report

def check_grafana(host='localhost', port=3000):
    """Check if Grafana is running"""
    print(f"{BLUE}Checking Grafana (http://{host}:{port})...{RESET}")
    
    report = ValidationReport()
    
    try:
        response = requests.get(f"http://{host}:{port}/api/health", 
                               timeout=5)
        
        if response.status_code == 200:
            report.add_check(f"Grafana Status", "PASS", 
                           f"http://{host}:{port}")
        else:
            report.add_check(f"Grafana Status", "FAIL", 
                           f"Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        report.add_check(f"Grafana Status", "WARN", 
                       f"Not running on http://{host}:{port} (use docker-compose)")
    except Exception as e:
        report.add_check(f"Grafana Status", "WARN", str(e))
    
    return report

def check_metrics_endpoint(host='localhost', port=5000):
    """Check if Prometheus metrics endpoint is available"""
    print(f"{BLUE}Checking Prometheus metrics endpoint...{RESET}")
    
    report = ValidationReport()
    
    try:
        response = requests.get(f"http://{host}:{port}/metrics", 
                               timeout=5,
                               headers={'X-API-Key': 'test-key'})
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            metric_lines = [l for l in lines if l and not l.startswith('#')]
            report.add_check(f"Metrics Endpoint", "PASS", 
                           f"{len(metric_lines)} metrics exported")
        else:
            report.add_check(f"Metrics Endpoint", "FAIL", 
                           f"Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        report.add_check(f"Metrics Endpoint", "FAIL", 
                       f"Cannot connect to http://{host}:{port}")
    except Exception as e:
        report.add_check(f"Metrics Endpoint", "FAIL", str(e))
    
    return report

def run_all_checks():
    """Run all validation checks"""
    
    print(f"\n{BLUE}{'='*60}")
    print("AI INTELLIGENCE ENGINE - VALIDATION SUITE")
    print(f"{'='*60}{RESET}\n")
    
    all_reports = []
    
    # File structure checks
    all_reports.append(check_backend_files())
    all_reports.append(check_frontend_files())
    
    # Package checks
    all_reports.append(check_python_packages())
    
    # Runtime checks
    all_reports.append(check_api_server())
    all_reports.append(check_prometheus())
    all_reports.append(check_grafana())
    all_reports.append(check_metrics_endpoint())
    
    # Combine all reports
    combined_report = ValidationReport()
    for report in all_reports:
        combined_report.checks.extend(report.checks)
    
    # Print summary
    success = combined_report.print_summary()
    
    # Print recommendations
    print(f"{BLUE}Recommendations:{RESET}")
    
    failed_checks = [c for c in combined_report.checks if c['status'] == 'FAIL']
    if not failed_checks:
        print(f"{GREEN}✓ All checks passed! System is ready.{RESET}")
        print(f"\n{BLUE}Next Steps:{RESET}")
        print("1. Start frontend: cd frontend && npm install && npm run dev")
        print("2. Start monitoring: docker-compose -f docker-compose-monitoring.yml up -d")
        print("3. Access dashboard: http://localhost:3000")
        print("4. Access Grafana: http://localhost:3000 (from docker-compose)")
    else:
        print(f"{RED}The following checks failed:{RESET}")
        for check in failed_checks:
            print(f"  - {check['name']}: {check['message']}")
    
    return success

if __name__ == "__main__":
    print(f"\n{BLUE}Starting validation...{RESET}\n")
    
    success = run_all_checks()
    
    sys.exit(0 if success else 1)
