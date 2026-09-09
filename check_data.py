#!/usr/bin/env python3
"""Check data generation results"""
import os
import pandas as pd

data_dir = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\data\raw"

print(f"Checking files in {data_dir}:\n")

for filename in sorted(os.listdir(data_dir)):
    filepath = os.path.join(data_dir, filename)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    if filename.endswith('.csv'):
        df = pd.read_csv(filepath)
        rows = len(df)
        print(f"  {filename:20} | {rows:8,} rows | {file_size_mb:8.2f} MB")

print("\n✓ Data generation complete!")
