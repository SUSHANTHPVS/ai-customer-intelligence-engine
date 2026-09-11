#!/usr/bin/env python3
"""Complete Phase 2 setup with diagnostics"""
import subprocess
import os
import sys
from pathlib import Path
import time

project_root = Path(r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine")
psql_exe = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

print("="*70)
print("PHASE 2: PostgreSQL Database Setup")
print("="*70)

# Check 1: Verify psql.exe exists
print("\n[CHECK 1] Verifying psql executable...")
if os.path.exists(psql_exe):
    print(f"  ✓ Found: {psql_exe}")
else:
    print(f"  ✗ Not found: {psql_exe}")
    sys.exit(1)

# Check 2: Test PostgreSQL version
print("\n[CHECK 2] Testing PostgreSQL version...")
try:
    result = subprocess.run(
        [psql_exe, "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print(f"  ✓ {result.stdout.strip()}")
    else:
        print(f"  ✗ Error: {result.stderr}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

# Check 3: Test connection
print("\n[CHECK 3] Testing PostgreSQL connection...")
try:
    result = subprocess.run(
        [psql_exe, "-U", "postgres", "-h", "localhost", "-c", "SELECT 1;"],
        capture_output=True,
        text=True,
        env={**os.environ, "PGPASSWORD": "postgres"},
        timeout=10
    )
    if result.returncode == 0:
        print("  ✓ Connection successful")
    else:
        if "password authentication failed" in result.stderr:
            print("  ✗ Password authentication failed")
            print("    Try a different password or reset PostgreSQL password")
        elif "could not connect" in result.stderr or "Connection refused" in result.stderr:
            print("  ✗ Cannot connect to server")
            print("    Make sure PostgreSQL service is running:")
            print("    Start-Service -Name postgresql-x64-18")
        else:
            print(f"  ✗ Error: {result.stderr[:200]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")
    sys.exit(1)

# Check 4: Verify CSV files exist
print("\n[CHECK 4] Verifying data files...")
csv_files = {
    "customers.csv": (project_root / "data" / "raw" / "customers.csv"),
    "events.csv": (project_root / "data" / "raw" / "events.csv"),
    "transactions.csv": (project_root / "data" / "raw" / "transactions.csv"),
    "support_tickets.csv": (project_root / "data" / "raw" / "support_tickets.csv"),
}

all_exist = True
for name, path in csv_files.items():
    if path.exists():
        size_mb = path.stat().st_size / (1024*1024)
        print(f"  ✓ {name} ({size_mb:.1f} MB)")
    else:
        print(f"  ✗ Missing: {name}")
        all_exist = False

if not all_exist:
    print("\n  Run data generation first: python src/data_generation/main.py")
    sys.exit(1)

# Check 5: Verify SQL schema files exist
print("\n[CHECK 5] Verifying SQL files...")
sql_files = {
    "schema.sql": (project_root / "sql" / "schema.sql"),
    "analytics.sql": (project_root / "sql" / "analytics.sql"),
}

for name, path in sql_files.items():
    if path.exists():
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ Missing: {name}")
        sys.exit(1)

# All checks passed
print("\n" + "="*70)
print("✓ All checks passed! Ready to run Phase 2 setup.")
print("="*70)

print("\nTo complete Phase 2, run:")
print("  python phase2_setup.py")
print("\nWhen prompted, enter password: postgres")
print("\nExpected setup time: 5-10 minutes")
print("\nFor manual setup, see: PHASE2_MANUAL_SETUP.md")
