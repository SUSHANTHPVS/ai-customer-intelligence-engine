#!/usr/bin/env python3
"""Check database status and write output to file"""
import psycopg2
import sys

output_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\database_check.txt"

with open(output_file, "w") as out:
    sys.stdout = out
    sys.stderr = out
    
    try:
        print("=" * 60)
        print("PostgreSQL Database Status Check")
        print("=" * 60)
        
        print("\nConnecting to PostgreSQL server...")
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
            
            print("\n✓ Phase 2 setup SUCCESSFUL!")
        else:
            print("\n✗ customer_intelligence database NOT FOUND")
            print("\nThe database needs to be created.")
            print("Run: python phase2_setup.py")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Check complete")
        print("=" * 60)
        
    except psycopg2.OperationalError as e:
        print(f"✗ Connection error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("Output written to database_check.txt", file=open(2, "w"))
