#!/usr/bin/env python3
"""Check Phase 2 setup completion status"""
import psycopg2
import json
from datetime import datetime
import os

def check_phase2_status():
    """Check if Phase 2 setup completed successfully"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "checking",
        "database_exists": False,
        "tables_created": [],
        "row_counts": {},
        "errors": []
    }
    
    try:
        # Try to connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="customer_intelligence"
        )
        
        cursor = conn.cursor()
        result["database_exists"] = True
        result["status"] = "success"
        
        # Check for expected tables
        tables_to_check = [
            "dim_customer",
            "dim_date", 
            "dim_product",
            "dim_campaign",
            "fact_events",
            "fact_transactions",
            "fact_support",
            "fact_marketing"
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                result["tables_created"].append(table)
                result["row_counts"][table] = count
            except Exception as e:
                result["errors"].append(f"Error reading {table}: {str(e)}")
        
        cursor.close()
        conn.close()
        
        # Determine overall status
        if len(result["tables_created"]) == len(tables_to_check):
            result["status"] = "PHASE_2_COMPLETE"
        elif len(result["tables_created"]) > 0:
            result["status"] = "PHASE_2_IN_PROGRESS"
        
    except psycopg2.OperationalError as e:
        result["status"] = "DATABASE_NOT_CREATED_YET"
        result["errors"].append(f"Connection error: {str(e)}")
    except Exception as e:
        result["status"] = "ERROR"
        result["errors"].append(f"Unexpected error: {str(e)}")
    
    return result

if __name__ == "__main__":
    status = check_phase2_status()
    
    # Write to JSON file
    json_file = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\phase2_status.json"
    with open(json_file, "w") as f:
        json.dump(status, f, indent=2)
    
    # Also print results
    print(json.dumps(status, indent=2))
