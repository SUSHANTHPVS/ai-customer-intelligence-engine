#!/usr/bin/env python3
"""Find PostgreSQL and update phase2_setup.py"""
import os
from pathlib import Path

# Common PostgreSQL installation paths
psql_paths = [
    r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
    r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
    r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
    r"C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe",
    r"C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe",
    r"C:\Program Files (x86)\PostgreSQL\14\bin\psql.exe",
]

print("Finding PostgreSQL installation...\n")

found_psql = None
for path in psql_paths:
    if os.path.exists(path):
        print(f"✓ FOUND: {path}")
        found_psql = path
        break
    else:
        print(f"✗ Not found: {path}")

if found_psql:
    print(f"\n✓ PostgreSQL found at: {found_psql}")
    print(f"\nDirectory contents:")
    bin_dir = os.path.dirname(found_psql)
    for f in os.listdir(bin_dir)[:10]:
        print(f"  - {f}")
    
    # Test connection
    print("\nTesting connection with default password 'postgres'...")
    import subprocess
    try:
        result = subprocess.run(
            [found_psql, "-U", "postgres", "-h", "localhost", "-c", "SELECT version();"],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": "postgres"},
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ Connection successful with password 'postgres'\n")
            print(result.stdout)
        else:
            print("✗ Connection failed")
            if "password authentication failed" in result.stderr:
                print("  Password 'postgres' is incorrect")
                print("  You may need to enter a different password when running phase2_setup.py")
            else:
                print(f"  Error: {result.stderr[:200]}")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("\n✗ PostgreSQL installation not found")
    print("\nPlease ensure PostgreSQL is installed. Check:")
    print("  1. Control Panel > Programs > Installed Programs (look for PostgreSQL)")
    print("  2. If found, note the version number (14, 15, 16, etc.)")
    print("  3. Check: C:\\Program Files\\PostgreSQL\\<VERSION>\\bin\\psql.exe")

print("\nNote: Run 'python phase2_setup.py' when ready")
