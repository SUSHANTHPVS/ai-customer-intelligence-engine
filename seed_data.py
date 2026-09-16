"""
Database seeding script - Creates and populates feature tables with sample data
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import random
import os
import time

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}

def seed_database():
    """Create and populate feature tables with sample data"""
    try:
        conn = None
        for attempt in range(12):
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                break
            except psycopg2.OperationalError:
                if attempt == 11:
                    raise
                time.sleep(min(5 * (attempt + 1), 15))
        cur = conn.cursor()
        
        print("[Seed] Connecting to database...")
        
        # Create feature_rfm table
        print("[Seed] Creating feature_rfm table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_rfm (
                customer_id VARCHAR(50) PRIMARY KEY,
                recency INTEGER,
                frequency INTEGER,
                monetary DECIMAL(12,2),
                rfm_segment VARCHAR(50),
                lifetime_value DECIMAL(12,2),
                predicted_ltv DECIMAL(12,2),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create feature_behavioral table
        print("[Seed] Creating feature_behavioral table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_behavioral (
                customer_id VARCHAR(50) PRIMARY KEY,
                avg_session_duration INTEGER,
                login_frequency INTEGER,
                feature_adoption_count INTEGER,
                last_active_date DATE,
                days_since_signup INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create feature_engagement table
        print("[Seed] Creating feature_engagement table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_engagement (
                customer_id VARCHAR(50) PRIMARY KEY,
                engagement_score DECIMAL(5,2),
                segment VARCHAR(50),
                active_days_last_30 INTEGER,
                feature_usage_count INTEGER,
                last_engagement DATE,
                engagement_trend VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create feature_revenue table
        print("[Seed] Creating feature_revenue table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_revenue (
                customer_id VARCHAR(50) PRIMARY KEY,
                total_revenue DECIMAL(12,2),
                avg_order_value DECIMAL(10,2),
                subscription_plan VARCHAR(100),
                mrr DECIMAL(10,2),
                arr DECIMAL(12,2),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create feature_support table
        print("[Seed] Creating feature_support table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_support (
                customer_id VARCHAR(50) PRIMARY KEY,
                total_tickets INTEGER,
                avg_resolution_time DECIMAL(8,2),
                satisfaction_score DECIMAL(3,2),
                support_tier VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create feature_churn_risk table
        print("[Seed] Creating feature_churn_risk table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_churn_risk (
                customer_id VARCHAR(50) PRIMARY KEY,
                churn_risk_score DECIMAL(5,2),
                churn_risk_category VARCHAR(50),
                risk_level VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Check if we already have data
        cur.execute("SELECT COUNT(*) as count FROM feature_engagement")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"[Seed] Database already has {count} engagement records. Skipping data seeding.")
            conn.commit()
            cur.close()
            conn.close()
            return
        
        print("[Seed] Seeding sample data...")
        
        # Generate sample customers and data
        segments = ['VIP', 'STANDARD', 'AT_RISK']
        risk_levels = ['LOW', 'MEDIUM', 'HIGH']
        subscription_plans = ['Free', 'Pro', 'Enterprise']
        engagement_trends = ['Increasing', 'Stable', 'Decreasing']
        
        num_customers = 50
        
        for i in range(num_customers):
            customer_id = f"CUST_{i+1:04d}"
            
            # Engagement data
            segment = random.choice(segments)
            engagement_score = round(random.uniform(20, 100), 2)
            active_days = random.randint(1, 30)
            feature_usage = random.randint(5, 100)
            engagement_trend = random.choice(engagement_trends)
            
            cur.execute("""
                INSERT INTO feature_engagement 
                (customer_id, engagement_score, segment, active_days_last_30, feature_usage_count, engagement_trend)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, engagement_score, segment, active_days, feature_usage, engagement_trend))
            
            # Revenue data
            plan = random.choice(subscription_plans)
            total_revenue = random.uniform(100, 5000)
            avg_order = total_revenue / random.randint(2, 10)
            mrr = total_revenue / 12
            
            cur.execute("""
                INSERT INTO feature_revenue 
                (customer_id, total_revenue, avg_order_value, subscription_plan, mrr, arr)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, total_revenue, avg_order, plan, mrr, total_revenue))
            
            # RFM data
            recency = random.randint(0, 90)
            frequency = random.randint(1, 100)
            monetary = round(random.uniform(50, 2000), 2)
            ltv = monetary * frequency
            
            cur.execute("""
                INSERT INTO feature_rfm 
                (customer_id, recency, frequency, monetary, lifetime_value, predicted_ltv, rfm_segment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, recency, frequency, monetary, ltv, ltv * 1.1, segment))
            
            # Churn risk data
            churn_score = round(random.uniform(0, 100), 2)
            if churn_score < 30:
                risk_level = 'LOW'
            elif churn_score < 70:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            cur.execute("""
                INSERT INTO feature_churn_risk 
                (customer_id, churn_risk_score, churn_risk_category, risk_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, churn_score, segment, risk_level))
            
            # Support data
            tickets = random.randint(0, 10)
            resolution_time = random.uniform(2, 48) if tickets > 0 else 0
            satisfaction = random.uniform(3, 5) if tickets > 0 else 0
            
            cur.execute("""
                INSERT INTO feature_support 
                (customer_id, total_tickets, avg_resolution_time, satisfaction_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, tickets, resolution_time, satisfaction))
            
            # Behavioral data
            session_duration = random.randint(5, 180)
            login_freq = random.randint(1, 30)
            feature_adoption = random.randint(1, 20)
            days_since_signup = random.randint(10, 730)
            
            cur.execute("""
                INSERT INTO feature_behavioral 
                (customer_id, avg_session_duration, login_frequency, feature_adoption_count, days_since_signup)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, (customer_id, session_duration, login_freq, feature_adoption, days_since_signup))
        
        conn.commit()
        print(f"[Seed] Successfully seeded {num_customers} customer records")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM feature_engagement")
        engagement_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM feature_churn_risk")
        churn_count = cur.fetchone()[0]
        
        print(f"[Seed] Verification: {engagement_count} engagement records, {churn_count} churn records")
        
        cur.close()
        conn.close()
        print("[Seed] Database seeding complete!")
        
    except Exception as e:
        print(f"[Seed] Error: {e}")
        raise

if __name__ == '__main__':
    seed_database()
