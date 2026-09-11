#!/usr/bin/env python3
"""Test PostgreSQL connection"""
import subprocess
import os
from pathlib import Path

psql_exe = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

print("Testing PostgreSQL connection...")
print(f"psql path: {psql_exe}")
print(f"psql exists: {os.path.exists(psql_exe)}")

# Test 1: Version check
print("\n[Test 1] Checking PostgreSQL version...")
try:
    result = subprocess.run(
        [psql_exe, "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"Return code: {result.returncode}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Exception: {e}")

# Test 2: Connection test
print("\n[Test 2] Testing database connection...")
try:
    result = subprocess.run(
        [psql_exe, "-U", "postgres", "-h", "localhost", "-c", "SELECT version();"],
        capture_output=True,
        text=True,
        env={**os.environ, "PGPASSWORD": "postgres"},
        timeout=10
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        print("✓ Connection successful!")
        print(f"Output: {result.stdout[:200]}")
    else:
        print("✗ Connection failed")
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Exception: {e}")

# Test 3: List databases
print("\n[Test 3] Listing databases...")
try:
    result = subprocess.run(
        [psql_exe, "-U", "postgres", "-h", "localhost", "-l"],
        capture_output=True,
        text=True,
        env={**os.environ, "PGPASSWORD": "postgres"},
        timeout=10
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        print("✓ Database list retrieved")
        lines = result.stdout.split('\n')[:15]
        for line in lines:
            print(line)
    else:
        print("✗ Failed to list databases")
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*60)
print("Connection test complete. Results saved above.")
