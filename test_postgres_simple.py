#!/usr/bin/env python3
"""Test PostgreSQL connection and write output to file"""
import subprocess
import os
import sys

psql_exe = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
output_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\postgres_test.txt"

with open(output_file, "w") as f:
    f.write("PostgreSQL Connection Test\n")
    f.write("="*60 + "\n\n")
    
    # Test 1: Version check
    f.write("[Test 1] Checking PostgreSQL version...\n")
    try:
        result = subprocess.run(
            [psql_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"Output: {result.stdout}\n")
        if result.stderr:
            f.write(f"Error: {result.stderr}\n")
    except Exception as e:
        f.write(f"Exception: {e}\n")
    
    # Test 2: Connection test
    f.write("\n[Test 2] Testing database connection...\n")
    try:
        result = subprocess.run(
            [psql_exe, "-U", "postgres", "-h", "localhost", "-c", "SELECT version();"],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": "postgres"},
            timeout=10
        )
        f.write(f"Return code: {result.returncode}\n")
        if result.returncode == 0:
            f.write("✓ Connection successful!\n")
            f.write(f"Output:\n{result.stdout}\n")
        else:
            f.write("✗ Connection failed\n")
            f.write(f"Error: {result.stderr}\n")
    except Exception as e:
        f.write(f"Exception: {e}\n")
    
    # Test 3: List databases
    f.write("\n[Test 3] Listing databases...\n")
    try:
        result = subprocess.run(
            [psql_exe, "-U", "postgres", "-h", "localhost", "-l"],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": "postgres"},
            timeout=10
        )
        f.write(f"Return code: {result.returncode}\n")
        if result.returncode == 0:
            f.write("✓ Database list retrieved\n")
            f.write(result.stdout + "\n")
        else:
            f.write("✗ Failed to list databases\n")
            f.write(f"Error: {result.stderr}\n")
    except Exception as e:
        f.write(f"Exception: {e}\n")
    
    f.write("\n" + "="*60 + "\n")
    f.write("Connection test complete.\n")

print(f"Test output written to: {output_file}")
