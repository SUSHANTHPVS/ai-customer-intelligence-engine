#!/usr/bin/env python3
"""Check PostgreSQL and write results to file"""
import subprocess
import os

output_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\postgres_check.txt"

with open(output_file, "w") as f:
    f.write("PostgreSQL Installation Check\n")
    f.write("=" * 70 + "\n\n")
    
    # Check if psql is available
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            f.write(f"✓ PostgreSQL found: {result.stdout.strip()}\n")
            f.write("STATUS: PostgreSQL is installed\n")
        else:
            f.write(f"✗ psql returned error: {result.stderr.strip()}\n")
            f.write("STATUS: PostgreSQL NOT found\n")
    except FileNotFoundError:
        f.write("✗ PostgreSQL not found in PATH\n")
        f.write("STATUS: PostgreSQL NOT found\n")
    except Exception as e:
        f.write(f"✗ Error: {e}\n")
        f.write("STATUS: PostgreSQL NOT found\n")
    
    # Check paths
    f.write("\nCommon installation paths:\n")
    paths = [
        r"C:\Program Files\PostgreSQL",
        r"C:\Program Files (x86)\PostgreSQL",
    ]
    
    for path in paths:
        if os.path.exists(path):
            f.write(f"  ✓ {path}\n")
        else:
            f.write(f"  ✗ {path}\n")
    
    f.write("\nNext step: Review this file\n")

print("Results written to postgres_check.txt")
