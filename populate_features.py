#!/usr/bin/env python3
"""
Populate feature tables from raw database tables - CORRECTED for actual schema.
"""
import psycopg2
from datetime import datetime, timedelta
import sys

DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'customer_intelligence',
    'user': 'postgres',
    'password': 'sushanth123'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def to_float(val):
    """Safely convert to float"""
    if val is None:
        return 0.0
    return float(val)

def to_int(val):
    """Safely convert to int"""
    if val is None:
        return 0
    return int(val)

def populate_features():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT customer_id FROM customers ORDER BY customer_id")
        customers = [row[0] for row in cursor.fetchall()]
        total = len(customers)
        
        print(f"[Populate] Found {total} customers to process")
        
        today = datetime.now().date()
        
        for idx, customer_id in enumerate(customers):
            if (idx + 1) % 1000 == 0:
                print(f"[Populate] Processing customer {idx + 1}/{total}")
                conn.commit()
            
            # ============ RFM FEATURES ============
            cursor.execute("""
                SELECT 
                    COALESCE(MAX(transaction_timestamp)::date, CURRENT_DATE) as recency_date,
                    COUNT(DISTINCT transaction_id) as frequency,
                    COALESCE(SUM(amount), 0)::numeric(12,2) as monetary
                FROM transactions
                WHERE customer_id = %s
            """, (customer_id,))
            
            rfm_result = cursor.fetchone()
            recency_date, frequency, monetary = rfm_result
            recency = (today - recency_date).days if recency_date else 999
            frequency = to_int(frequency)
            monetary = to_float(monetary)
            
            lifetime_value = monetary
            predicted_ltv = monetary * (1 + frequency * 0.1) if frequency > 0 else 0
            
            # RFM segment logic
            if frequency > 20 and recency < 30 and monetary > 1000:
                rfm_segment = 'VIP'
            elif frequency > 10 and recency < 60 and monetary > 500:
                rfm_segment = 'Active'
            elif recency > 120:
                rfm_segment = 'Dormant'
            else:
                rfm_segment = 'Regular'
            
            # ============ BEHAVIORAL FEATURES ============
            cursor.execute("""
                SELECT 
                    COALESCE(AVG(session_duration_seconds), 0)::integer as avg_session,
                    COUNT(DISTINCT event_timestamp::date) as login_freq,
                    COUNT(DISTINCT CASE WHEN event_type = 'feature_adoption' THEN event_type END) as feature_count,
                    COALESCE(MAX(event_timestamp::date), CURRENT_DATE) as last_active
                FROM events
                WHERE customer_id = %s
            """, (customer_id,))
            
            behav_result = cursor.fetchone()
            avg_session_duration, login_freq, feature_count, last_active = behav_result
            avg_session_duration = to_int(avg_session_duration)
            login_freq = to_int(login_freq)
            feature_count = to_int(feature_count)
            days_since_signup = (today - last_active).days if last_active else 999
            
            # ============ ENGAGEMENT FEATURES ============
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN event_timestamp > NOW() - INTERVAL '30 days' THEN event_id END) as active_30,
                    COUNT(DISTINCT event_type) as feature_usage,
                    COUNT(*) as total_events
                FROM events
                WHERE customer_id = %s
            """, (customer_id,))
            
            eng_result = cursor.fetchone()
            active_30, feature_usage, total_events = eng_result
            active_30 = to_int(active_30)
            feature_usage = to_int(feature_usage)
            total_events = to_int(total_events)
            
            engagement_score = min(100.0, (active_30 * 2) + (feature_usage * 3) + max(0, login_freq / 10.0))
            
            if engagement_score >= 70 and monetary >= 500:
                segment = 'VIP'
            elif engagement_score < 30 or recency > 90:
                segment = 'AT_RISK'
            elif total_events == 0:
                segment = 'DORMANT'
            else:
                segment = 'STANDARD'
            
            last_engagement = last_active
            engagement_trend = 'upward' if active_30 > login_freq / 10 else ('stable' if active_30 == login_freq / 10 else 'downward')
            
            # ============ REVENUE FEATURES ============
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(amount), 0)::numeric(12,2) as total_revenue,
                    COUNT(*) as order_count,
                    COALESCE(MAX(subscription_plan), 'basic') as subscription,
                    COALESCE(AVG(amount), 0)::numeric(10,2) as avg_order_val
                FROM transactions
                WHERE customer_id = %s
            """, (customer_id,))
            
            rev_result = cursor.fetchone()
            total_rev, order_count, subscription, avg_order_val = rev_result
            total_rev = to_float(total_rev)
            order_count = to_int(order_count)
            avg_order_val = to_float(avg_order_val)
            
            mrr = round(total_rev / 12.0, 2) if order_count > 0 else 0
            arr = total_rev if order_count > 0 else 0
            
            # ============ SUPPORT FEATURES ============
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COALESCE(AVG(resolution_time_hours), 0)::numeric(8,2) as avg_resolution,
                    COALESCE(AVG(satisfaction_score), 0)::numeric(3,2) as satisfaction
                FROM support_tickets
                WHERE customer_id = %s
            """, (customer_id,))
            
            supp_result = cursor.fetchone()
            total_tickets, avg_resolution, satisfaction = supp_result
            total_tickets = to_int(total_tickets)
            avg_resolution = to_float(avg_resolution)
            satisfaction = to_float(satisfaction)
            
            support_tier = 'premium' if total_tickets > 5 else 'standard'
            
            # ============ CHURN RISK FEATURES ============
            if recency > 60:
                churn_risk_score = 0.90
            elif recency > 30:
                churn_risk_score = 0.60
            elif engagement_score < 30:
                churn_risk_score = 0.70
            else:
                churn_risk_score = max(0.0, 0.50 - (engagement_score / 200.0))
            
            risk_level = 'HIGH' if churn_risk_score >= 0.7 else ('MEDIUM' if churn_risk_score >= 0.4 else 'LOW')
            churn_risk_category = risk_level
            
            # ============ INSERT INTO FEATURE TABLES ============
            cursor.execute("""
                INSERT INTO feature_rfm (customer_id, recency, frequency, monetary, 
                    rfm_segment, lifetime_value, predicted_ltv)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    recency = EXCLUDED.recency, frequency = EXCLUDED.frequency,
                    monetary = EXCLUDED.monetary, rfm_segment = EXCLUDED.rfm_segment,
                    lifetime_value = EXCLUDED.lifetime_value, predicted_ltv = EXCLUDED.predicted_ltv
            """, (customer_id, recency, frequency, monetary, rfm_segment, lifetime_value, predicted_ltv))
            
            cursor.execute("""
                INSERT INTO feature_behavioral (customer_id, avg_session_duration, 
                    login_frequency, feature_adoption_count, days_since_signup)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    avg_session_duration = EXCLUDED.avg_session_duration, 
                    login_frequency = EXCLUDED.login_frequency,
                    feature_adoption_count = EXCLUDED.feature_adoption_count, 
                    days_since_signup = EXCLUDED.days_since_signup
            """, (customer_id, avg_session_duration, login_freq, feature_count, days_since_signup))
            
            cursor.execute("""
                INSERT INTO feature_engagement (customer_id, engagement_score, segment, 
                    active_days_last_30, feature_usage_count, last_engagement, engagement_trend)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    engagement_score = EXCLUDED.engagement_score, segment = EXCLUDED.segment,
                    active_days_last_30 = EXCLUDED.active_days_last_30, 
                    feature_usage_count = EXCLUDED.feature_usage_count,
                    last_engagement = EXCLUDED.last_engagement, 
                    engagement_trend = EXCLUDED.engagement_trend
            """, (customer_id, engagement_score, segment, active_30, feature_usage, last_engagement, engagement_trend))
            
            cursor.execute("""
                INSERT INTO feature_revenue (customer_id, total_revenue, avg_order_value, 
                    subscription_plan, mrr, arr)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue, avg_order_value = EXCLUDED.avg_order_value,
                    subscription_plan = EXCLUDED.subscription_plan, mrr = EXCLUDED.mrr, 
                    arr = EXCLUDED.arr
            """, (customer_id, total_rev, avg_order_val, subscription, mrr, arr))
            
            cursor.execute("""
                INSERT INTO feature_support (customer_id, total_tickets, 
                    avg_resolution_time, satisfaction_score, support_tier)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    total_tickets = EXCLUDED.total_tickets, 
                    avg_resolution_time = EXCLUDED.avg_resolution_time,
                    satisfaction_score = EXCLUDED.satisfaction_score, 
                    support_tier = EXCLUDED.support_tier
            """, (customer_id, total_tickets, avg_resolution, satisfaction, support_tier))
            
            cursor.execute("""
                INSERT INTO feature_churn_risk (customer_id, churn_risk_score, 
                    churn_risk_category, risk_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    churn_risk_score = EXCLUDED.churn_risk_score, 
                    churn_risk_category = EXCLUDED.churn_risk_category,
                    risk_level = EXCLUDED.risk_level
            """, (customer_id, churn_risk_score, churn_risk_category, risk_level))
        
        conn.commit()
        print(f"[Populate] ✓ Successfully populated feature tables for all {total} customers")
        
        # Verify counts
        cursor.execute("SELECT COUNT(*) FROM feature_rfm")
        rfm_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM feature_engagement")
        eng_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM feature_churn_risk")
        churn_count = cursor.fetchone()[0]
        print(f"[Verify] RFM: {rfm_count}, Engagement: {eng_count}, Churn Risk: {churn_count}")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("POPULATING FEATURE TABLES FROM RAW DATA")
    print("=" * 70)
    populate_features()
    print("=" * 70)
    print("✓ Feature population complete!")
    print("=" * 70)
