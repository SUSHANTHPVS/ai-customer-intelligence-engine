#!/usr/bin/env python3
"""Direct PostgreSQL check - see if Phase 2 database exists"""
import psycopg2
import json
from datetime import datetime

result = {"timestamp": datetime.now().isoformat()}

try:
    # Try to connect to default postgres database first
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    cursor = conn.cursor()
    
    # Check if customer_intelligence database exists
    cursor.execute("""
        SELECT datname FROM pg_database 
        WHERE datname = 'customer_intelligence'
    """)
    
    db_exists = cursor.fetchone() is not None
    result["database_exists"] = db_exists
    result["status"] = "SUCCESS" if db_exists else "DATABASE_NOT_CREATED"
    
    if db_exists:
        # Try to connect to it
        cursor.close()
        conn.close()
        
        conn2 = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="customer_intelligence"
        )
        cursor2 = conn2.cursor()
        
        # Check tables
        cursor2.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor2.fetchall()]
        result["tables"] = tables
        result["table_count"] = len(tables)
        
        # Get row counts for each table
        row_counts = {}
        for table in tables:
            try:
                cursor2.execute(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = cursor2.fetchone()[0]
            except:
                row_counts[table] = None
        
        result["row_counts"] = row_counts
        
        cursor2.close()
        conn2.close()
    else:
        cursor.close()
        conn.close()
    
except Exception as e:
    result["status"] = f"ERROR: {str(e)}"

# Write to file and print
import os
output_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\postgres_check_result.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w") as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
