#!/usr/bin/env python3
"""Quick test of data generator"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    print("\n1. Loading config...")
    from src.utils.config import RAW_DATA_DIR, CUSTOMERS_COUNT
    print(f"   RAW_DATA_DIR: {RAW_DATA_DIR}")
    print(f"   CUSTOMERS_COUNT: {CUSTOMERS_COUNT}")
    
    print("\n2. Loading generator...")
    from src.data_generation.generator import SyntheticDataGenerator
    print("   Generator loaded successfully")
    
    print("\n3. Creating generator instance...")
    gen = SyntheticDataGenerator(num_customers=100, num_events=1000)  # Small dataset for testing
    print("   Instance created")
    
    print("\n4. Running generation...")
    customers, events, transactions, tickets = gen.generate_all()
    print(f"   Generated {len(customers)} customers, {len(events)} events, {len(transactions)} transactions, {len(tickets)} tickets")
    
    print("\n5. Checking data directory...")
    import os
    if os.path.exists(RAW_DATA_DIR):
        files = os.listdir(RAW_DATA_DIR)
        print(f"   Files in {RAW_DATA_DIR}: {files}")
    else:
        print(f"   Directory {RAW_DATA_DIR} does not exist!")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
