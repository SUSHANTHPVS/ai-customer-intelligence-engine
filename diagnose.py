#!/usr/bin/env python3
"""Quick diagnostic script to check churn risk data"""

import psycopg2
import os

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='customer_intelligence',
    user='postgres',
    password=os.environ.get('PGPASSWORD', 'sushanth123')
)

cursor = conn.cursor()

# Check churn_risk_category values
cursor.execute("""
    SELECT DISTINCT churn_risk_category, COUNT(*) 
    FROM feature_churn_risk 
    GROUP BY churn_risk_category 
    ORDER BY COUNT(*) DESC;
""")

print("Churn Risk Category Distribution:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check if there's any HIGH or CRITICAL
cursor.execute("""
    SELECT churn_risk_category, COUNT(*) 
    FROM feature_churn_risk 
    WHERE churn_risk_category IN ('HIGH', 'CRITICAL')
    GROUP BY churn_risk_category;
""")

result = cursor.fetchall()
print(f"\nHIGH/CRITICAL count: {len(result)}")
for row in result:
    print(f"  {row[0]}: {row[1]}")

conn.close()
