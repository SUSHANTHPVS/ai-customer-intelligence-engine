#!/usr/bin/env python3
"""Check PostgreSQL installation and provide setup instructions"""
import subprocess
import os
import sys

print("=" * 70)
print("PostgreSQL Installation Check")
print("=" * 70)

# Check if psql is available
try:
    result = subprocess.run(["psql", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"\n✓ PostgreSQL found: {result.stdout.strip()}")
        psql_available = True
    else:
        print(f"\n✗ psql command returned error: {result.stderr.strip()}")
        psql_available = False
except FileNotFoundError:
    print("\n✗ PostgreSQL not found in PATH")
    psql_available = False
except Exception as e:
    print(f"\n✗ Error checking PostgreSQL: {e}")
    psql_available = False

# Check common installation paths
print("\nChecking common installation paths:")
common_paths = [
    r"C:\Program Files\PostgreSQL",
    r"C:\Program Files (x86)\PostgreSQL",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\16\bin",
]

found_paths = []
for path in common_paths:
    if os.path.exists(path):
        print(f"  ✓ Found: {path}")
        found_paths.append(path)
    else:
        print(f"  ✗ Not found: {path}")

print("\n" + "=" * 70)
if psql_available:
    print("STATUS: PostgreSQL is installed and available")
    print("\nNext steps:")
    print("1. Verify you can connect: psql -U postgres")
    print("2. Create database: CREATE DATABASE customer_intelligence;")
    print("3. Load schema: psql -U postgres -d customer_intelligence -f sql/schema.sql")
else:
    print("STATUS: PostgreSQL is NOT installed")
    print("\nTo install PostgreSQL on Windows:")
    print("1. Download installer from: https://www.postgresql.org/download/windows/")
    print("2. Run the installer (choose PostgreSQL 14 or newer)")
    print("3. During installation:")
    print("   - Set password for postgres user")
    print("   - Accept default port 5432")
    print("   - Include pgAdmin (optional but recommended)")
    print("4. After installation, restart your terminal")
    print("5. Run this script again to verify")
    print("\nAlternatively, install via package manager:")
    print("  - Using chocolatey: choco install postgresql")
    print("  - Using winget: winget install PostgreSQL.PostgreSQL")

print("\n" + "=" * 70)
print("Configuration file location: C:\\Users\\SUSHANTH\\Desktop\\AI Customer Intelligence Engine\\.env")
print("Database connection string will be:")
print("  postgresql://postgres:<password>@localhost:5432/customer_intelligence")
print("=" * 70 + "\n")

sys.exit(0 if psql_available else 1)
