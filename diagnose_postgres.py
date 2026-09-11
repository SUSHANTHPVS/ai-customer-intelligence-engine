#!/usr/bin/env python3
"""Find PostgreSQL installation and verify it's running"""
import os
import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("PostgreSQL Installation Diagnostic")
print("=" * 70)

# Common PostgreSQL installation paths on Windows
common_paths = [
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files (x86)\PostgreSQL\15\bin",
    r"C:\Program Files (x86)\PostgreSQL\14\bin",
]

print("\nSearching for PostgreSQL installation...")
found_psql = None

for path in common_paths:
    psql_path = os.path.join(path, "psql.exe")
    if os.path.exists(psql_path):
        print(f"  FOUND: {psql_path}")
        found_psql = psql_path
        break
    else:
        print(f"  NOT FOUND: {path}")

if not found_psql:
    print("\n  Checking if psql is in PATH...")
    try:
        result = subprocess.run(["where", "psql"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            found_psql = result.stdout.strip().split('\n')[0]
            print(f"  FOUND in PATH: {found_psql}")
        else:
            print("  NOT in PATH")
    except:
        pass

print("\n" + "-" * 70)
print("PostgreSQL Service Status")
print("-" * 70)

# Check Windows service
try:
    result = subprocess.run(
        ["sc", "query", "postgresql-x64-15"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if "RUNNING" in result.stdout:
        print("  PostgreSQL service (15): RUNNING")
    elif "STOPPED" in result.stdout:
        print("  PostgreSQL service (15): STOPPED")
        print("\n  To start the service, run in Admin PowerShell:")
        print("    Start-Service -Name postgresql-x64-15")
    else:
        print("  PostgreSQL service (15): Unknown status")
except:
    print("  Could not check service status")

print("\n" + "-" * 70)
print("Testing Connection")
print("-" * 70)

if found_psql:
    print(f"Using: {found_psql}\n")
    
    # Try to connect with default password
    try:
        result = subprocess.run(
            [found_psql, "-U", "postgres", "-h", "localhost", "-c", "SELECT version();"],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": "postgres"},
            timeout=5
        )
        
        if result.returncode == 0:
            print("  SUCCESS: Connected with password 'postgres'")
            print("\n  PostgreSQL Version:")
            for line in result.stdout.split('\n'):
                if 'PostgreSQL' in line:
                    print(f"    {line.strip()}")
        else:
            if "password authentication failed" in result.stderr:
                print("  FAILED: Password is incorrect")
                print("  Please check what password you set during installation")
            elif "could not connect" in result.stderr or "Connection refused" in result.stderr:
                print("  FAILED: Cannot connect to PostgreSQL")
                print("  PostgreSQL service may not be running")
            else:
                print(f"  FAILED: {result.stderr[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  PostgreSQL installation not found in standard paths")
    print("\n  Please:")
    print("  1. Verify PostgreSQL was installed")
    print("  2. Check Control Panel > Programs > Installed Programs for PostgreSQL")
    print("  3. Note the installation path")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

if found_psql:
    print("\n1. Add PostgreSQL to your PATH (so 'psql' works everywhere):")
    print(f"   setx PATH \"%PATH%;{os.path.dirname(found_psql)}\"")
    print("   (Requires restart of terminal)")
    print("\n2. Or use the full path in the Phase 2 script")
    print(f"   Update phase2_setup.py to use: {found_psql}")
    print("\n3. Verify password:")
    print("   Default is usually 'postgres'")
    print("   If different, update phase2_setup.py with correct password")
else:
    print("\nPostgreSQL installation not found.")
    print("Please reinstall PostgreSQL and ensure it's added to PATH")

print("\n" + "=" * 70)
