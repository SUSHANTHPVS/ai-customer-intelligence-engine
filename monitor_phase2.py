#!/usr/bin/env python3
"""Check Phase 2 progress by connecting to PostgreSQL"""
import psycopg2
import time
from datetime import datetime

def check_status():
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Phase 2 progress...\n")
        
        # Try to connect to customer_intelligence database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="postgres",
                database="customer_intelligence"
            )
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT COUNT(*) FROM dim_customer;")
            customer_count = cursor.fetchone()[0]
            print(f"✓ Database exists!")
            print(f"  Customers: {customer_count:,}")
            
            # Check events
            try:
                cursor.execute("SELECT COUNT(*) FROM fact_events;")
                events_count = cursor.fetchone()[0]
                print(f"  Events: {events_count:,}")
            except:
                print(f"  Events: (table being populated...)")
            
            cursor.close()
            conn.close()
            
            if customer_count > 0:
                print(f"\n✅ Phase 2 is PROGRESSING - Database created and data loading")
                return True
            
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                print("⏳ Database not yet created (Phase 2 still running...)")
                return False
            else:
                raise
    
    except Exception as e:
        print(f"⏳ Phase 2 still in progress... ({str(e)[:60]})")
        return False

# Check multiple times with delays
for i in range(1, 4):
    print(f"\nAttempt {i}/3:")
    if check_status():
        print("\n✅ SUCCESS - Database setup is progressing!")
        break
    if i < 3:
        print("  Waiting 10 seconds...")
        time.sleep(10)
