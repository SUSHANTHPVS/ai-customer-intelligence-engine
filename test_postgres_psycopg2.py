#!/usr/bin/env python3
"""Direct PostgreSQL connection test using psycopg2"""
import sys
import os

# Ensure psycopg2 is available
try:
    import psycopg2
    print("psycopg2 imported successfully")
except ImportError:
    print("psycopg2 not found, attempting to install...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=False)
    import psycopg2

try:
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    
    print("✓ Connection successful!")
    
    cursor = conn.cursor()
    
    # Get version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"\nPostgreSQL Version:\n{version[0]}\n")
    
    # List databases
    cursor.execute("""
        SELECT datname FROM pg_database 
        WHERE datistemplate = false 
        ORDER BY datname;
    """)
    
    print("Available databases:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ PostgreSQL is ready for Phase 2 setup!")
    
except psycopg2.OperationalError as e:
    print(f"✗ Connection failed: {e}")
    print("\nPossible reasons:")
    print("  1. PostgreSQL service not running")
    print("  2. Incorrect password (try 'postgres')")
    print("  3. Incorrect host or port")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
