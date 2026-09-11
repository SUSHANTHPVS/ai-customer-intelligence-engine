#!/usr/bin/env python3
"""Check if customer_intelligence database exists and has data"""
import psycopg2
from psycopg2 import sql

try:
    # First, connect to default postgres database to check
    print("Connecting to PostgreSQL server...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    
    cursor = conn.cursor()
    
    # List all databases
    cursor.execute("""
        SELECT datname FROM pg_database 
        WHERE datistemplate = false 
        ORDER BY datname;
    """)
    
    databases = cursor.fetchall()
    print("\nAvailable databases:")
    for row in databases:
        print(f"  - {row[0]}")
    
    # Check if customer_intelligence database exists
    customer_intelligence_exists = any(row[0] == "customer_intelligence" for row in databases)
    
    if customer_intelligence_exists:
        print("\n✓ customer_intelligence database FOUND!")
        
        # Connect to it
        conn.close()
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="customer_intelligence"
        )
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        
        tables = cursor.fetchall()
        print("\nTables in customer_intelligence:")
        for row in tables:
            table_name = row[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count:,} rows")
        
        print("\n✓ Database setup COMPLETE!")
    else:
        print("\n✗ customer_intelligence database NOT FOUND")
        print("\nPhase 2 setup may not have completed successfully.")
        print("Please run: python phase2_setup.py")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"✗ Connection error: {e}")
    print("\nMake sure PostgreSQL is running:")
    print("  Windows: Services > postgresql-x64-18 > Start")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
