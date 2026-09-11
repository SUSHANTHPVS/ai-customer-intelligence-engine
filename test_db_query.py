#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='customer_intelligence',
    user='postgres',
    password='sushanth123'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

query = '''
SELECT 
    c.customer_id,
    c.country,
    c.industry,
    c.acquisition_channel,
    rf.rfm_score,
    rf.rfm_segment,
    rf.recency_days,
    rf.frequency_transactions,
    rf.monetary_value,
    bh.total_events,
    bh.unique_event_types,
    bh.unique_features_used,
    bh.avg_session_duration,
    bh.login_frequency,
    bh.feature_usage_premium_pct,
    en.engagement_score,
    en.days_since_signup,
    en.days_active,
    en.is_active_last_30days::INT,
    en.is_active_last_7days::INT,
    rv.total_revenue,
    rv.subscription_plan,
    rv.avg_transaction_value,
    rv.transaction_frequency,
    rv.failed_payment_count,
    rv.subscription_tenure_days,
    sp.total_tickets,
    sp.avg_resolution_hours,
    sp.avg_satisfaction_score,
    sp.critical_priority_count,
    sp.issue_resolution_rate,
    cr.churn_risk_score,
    cr.churn_risk_category,
    cr.days_inactive
FROM customers c
LEFT JOIN feature_rfm rf ON c.customer_id = rf.customer_id
LEFT JOIN feature_behavioral bh ON c.customer_id = bh.customer_id
LEFT JOIN feature_engagement en ON c.customer_id = en.customer_id
LEFT JOIN feature_revenue rv ON c.customer_id = rv.customer_id
LEFT JOIN feature_support sp ON c.customer_id = sp.customer_id
LEFT JOIN feature_churn_risk cr ON c.customer_id = cr.customer_id
WHERE c.customer_id = 'C000001'
'''

cur.execute(query)
result = cur.fetchone()
cur.close()
conn.close()

if result:
    data = dict(result)
    print("Returned columns:")
    for key, value in data.items():
        print(f"  {key}: {value} (type: {type(value).__name__ if value is not None else 'NULL'})")
    print(f"\nTotal columns: {len(data)}")
else:
    print("No result")
