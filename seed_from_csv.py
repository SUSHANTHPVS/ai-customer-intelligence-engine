"""
Database seeding script - Reads CSV files and populates PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import csv
from datetime import datetime, timedelta
import os
import sys

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}

CSV_BASE_PATH = '/data/raw' if os.path.exists('/data/raw') else 'data/raw'

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[Error] Failed to connect to database: {e}")
        return None

def seed_customers(conn):
    """Load customers from CSV"""
    try:
        print("[Seed] Loading customers from CSV...")
        cur = conn.cursor()
        csv_path = os.path.join(CSV_BASE_PATH, 'customers.csv')
        
        if not os.path.exists(csv_path):
            print(f"[Warn] Customers CSV not found at {csv_path}")
            return 0
        
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append((
                    row['customer_id'],
                    row['first_name'],
                    row['last_name'],
                    row['email'],
                    row['country'],
                    row['industry'],
                    row['acquisition_channel'],
                    row['signup_date']
                ))
        
        query = """
            INSERT INTO customers (customer_id, first_name, last_name, email, 
                                 country, industry, acquisition_channel, signup_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING
        """
        
        execute_batch(cur, query, records, page_size=500)
        conn.commit()
        print(f"[Seed] Loaded {len(records)} customers")
        return len(records)
    except Exception as e:
        print(f"[Error] Failed to seed customers: {e}")
        conn.rollback()
        return 0

def seed_events(conn):
    """Load events from CSV"""
    try:
        print("[Seed] Loading events from CSV...")
        cur = conn.cursor()
        csv_path = os.path.join(CSV_BASE_PATH, 'events.csv')
        
        if not os.path.exists(csv_path):
            print(f"[Warn] Events CSV not found at {csv_path}")
            return 0
        
        records = []
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append((
                    row['event_id'],
                    row['customer_id'],
                    row['event_type'],
                    row['feature'],
                    row['event_timestamp'],
                    int(row['session_duration_seconds']) if row['session_duration_seconds'] else 0,
                    float(row['event_value']) if row['event_value'] else 0.0
                ))
                count += 1
                if count % 5000 == 0:
                    print(f"[Seed] Processing events... {count} records")
        
        query = """
            INSERT INTO events (event_id, customer_id, event_type, feature, 
                              event_timestamp, session_duration_seconds, event_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
        """
        
        # Insert in batches
        for i in range(0, len(records), 1000):
            batch = records[i:i+1000]
            execute_batch(cur, query, batch, page_size=500)
            conn.commit()
        
        print(f"[Seed] Loaded {len(records)} events")
        return len(records)
    except Exception as e:
        print(f"[Error] Failed to seed events: {e}")
        conn.rollback()
        return 0

def seed_transactions(conn):
    """Load transactions from CSV"""
    try:
        print("[Seed] Loading transactions from CSV...")
        cur = conn.cursor()
        csv_path = os.path.join(CSV_BASE_PATH, 'transactions.csv')
        
        if not os.path.exists(csv_path):
            print(f"[Warn] Transactions CSV not found at {csv_path}")
            return 0
        
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append((
                    row['transaction_id'],
                    row['customer_id'],
                    row['transaction_type'],
                    row['subscription_plan'],
                    float(row['amount']) if row['amount'] else 0.0,
                    row['currency'],
                    row['payment_method'],
                    row['payment_status'],
                    row['transaction_timestamp']
                ))
        
        query = """
            INSERT INTO transactions (transaction_id, customer_id, transaction_type, 
                                     subscription_plan, amount, currency, payment_method, 
                                     payment_status, transaction_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO NOTHING
        """
        
        execute_batch(cur, query, records, page_size=500)
        conn.commit()
        print(f"[Seed] Loaded {len(records)} transactions")
        return len(records)
    except Exception as e:
        print(f"[Error] Failed to seed transactions: {e}")
        conn.rollback()
        return 0

def seed_support_tickets(conn):
    """Load support tickets from CSV"""
    try:
        print("[Seed] Loading support tickets from CSV...")
        cur = conn.cursor()
        csv_path = os.path.join(CSV_BASE_PATH, 'support_tickets.csv')
        
        if not os.path.exists(csv_path):
            print(f"[Warn] Support tickets CSV not found at {csv_path}")
            return 0
        
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append((
                    row['ticket_id'],
                    row['customer_id'],
                    row['category'],
                    row['priority'],
                    float(row['resolution_time_hours']) if row['resolution_time_hours'] else 0.0,
                    int(row['satisfaction_score']) if row['satisfaction_score'] else 0,
                    row['created_at']
                ))
        
        query = """
            INSERT INTO support_tickets (ticket_id, customer_id, category, priority, 
                                        resolution_time_hours, satisfaction_score, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticket_id) DO NOTHING
        """
        
        execute_batch(cur, query, records, page_size=500)
        conn.commit()
        print(f"[Seed] Loaded {len(records)} support tickets")
        return len(records)
    except Exception as e:
        print(f"[Error] Failed to seed support tickets: {e}")
        conn.rollback()
        return 0

def create_feature_tables(conn):
    """Create feature tables if they don't exist"""
    try:
        cur = conn.cursor()
        
        # feature_rfm
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
        
        # feature_behavioral
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
        
        # feature_engagement
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
        
        # feature_revenue
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
        
        # feature_support
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
        
        # feature_churn_risk
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_churn_risk (
                customer_id VARCHAR(50) PRIMARY KEY,
                churn_risk_score DECIMAL(5,2),
                churn_risk_category VARCHAR(50),
                risk_level VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        conn.commit()
        print("[Seed] Feature tables created successfully")
    except Exception as e:
        print(f"[Error] Failed to create feature tables: {e}")
        conn.rollback()

def populate_features_from_raw_data(conn):
    """Aggregate raw data into feature tables"""
    try:
        print("[Seed] Aggregating raw data into feature tables...")
        cur = conn.cursor()
        
        # Get all unique customers
        cur.execute("SELECT DISTINCT customer_id FROM customers ORDER BY customer_id")
        customers = [row[0] for row in cur.fetchall()]
        print(f"[Seed] Processing {len(customers)} customers...")
        
        for customer_id in customers:
            # RFM Features
            cur.execute("""
                SELECT
                    COALESCE(MAX(EXTRACT(DAY FROM (NOW() - t.transaction_timestamp))), 0)::INT as recency,
                    COALESCE(COUNT(t.transaction_id), 0)::INT as frequency,
                    COALESCE(SUM(t.amount), 0)::DECIMAL as monetary
                FROM transactions t
                WHERE t.customer_id = %s AND t.payment_status = 'completed'
            """, (customer_id,))
            
            rfm = cur.fetchone()
            if rfm and rfm[2] and rfm[2] > 0:  # Has monetary value
                recency, frequency, monetary = rfm
                lifetime_value = monetary * frequency if frequency > 0 else 0
                segment = 'VIP' if (recency < 30 and frequency > 5) else ('STANDARD' if frequency > 2 else 'AT_RISK')
                
                cur.execute("""
                    INSERT INTO feature_rfm (customer_id, recency, frequency, monetary, 
                                            rfm_segment, lifetime_value, predicted_ltv)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        recency = EXCLUDED.recency,
                        frequency = EXCLUDED.frequency,
                        monetary = EXCLUDED.monetary,
                        rfm_segment = EXCLUDED.rfm_segment,
                        lifetime_value = EXCLUDED.lifetime_value,
                        predicted_ltv = EXCLUDED.predicted_ltv
                """, (customer_id, recency, frequency, monetary, segment, lifetime_value, lifetime_value * 1.15))
            
            # Behavioral Features
            cur.execute("""
                SELECT
                    COALESCE(AVG(e.session_duration_seconds), 0)::INT as avg_session,
                    COALESCE(COUNT(DISTINCT DATE(e.event_timestamp)), 0)::INT as login_freq,
                    COALESCE(COUNT(DISTINCT e.feature), 0)::INT as feature_adoption,
                    COALESCE(MAX(DATE(e.event_timestamp)), CURRENT_DATE)::DATE as last_active
                FROM events e
                WHERE e.customer_id = %s
            """, (customer_id,))
            
            behav = cur.fetchone()
            if behav:
                avg_session, login_freq, feature_adoption, last_active = behav
                days_since_signup = cur.execute("""
                    SELECT EXTRACT(DAY FROM (CURRENT_DATE - c.signup_date::DATE))::INT
                    FROM customers c WHERE c.customer_id = %s
                """, (customer_id,)) or 0
                cur.execute("""
                    INSERT INTO feature_behavioral (customer_id, avg_session_duration, 
                                                   login_frequency, feature_adoption_count, 
                                                   last_active_date, days_since_signup)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        avg_session_duration = EXCLUDED.avg_session_duration,
                        login_frequency = EXCLUDED.login_frequency,
                        feature_adoption_count = EXCLUDED.feature_adoption_count,
                        last_active_date = EXCLUDED.last_active_date,
                        days_since_signup = EXCLUDED.days_since_signup
                """, (customer_id, avg_session or 0, login_freq or 0, feature_adoption or 0, 
                      last_active, 0))
            
            # Engagement Features
            cur.execute("""
                SELECT
                    COALESCE(COUNT(DISTINCT DATE(e.event_timestamp)), 0)::INT as active_days_30,
                    COALESCE(COUNT(e.event_id), 0)::INT as event_count,
                    COALESCE(MAX(DATE(e.event_timestamp)), CURRENT_DATE)::DATE as last_event
                FROM events e
                WHERE e.customer_id = %s AND e.event_timestamp > NOW() - INTERVAL '30 days'
            """, (customer_id,))
            
            eng = cur.fetchone()
            if eng:
                active_days_30, event_count, last_event = eng
                engagement_score = min(100, (active_days_30 * 2 + event_count * 0.5))
                segment = 'VIP' if engagement_score >= 70 else ('STANDARD' if engagement_score >= 40 else 'AT_RISK')
                trend = 'Increasing' if engagement_score > 50 else 'Stable'
                
                cur.execute("""
                    INSERT INTO feature_engagement (customer_id, engagement_score, segment, 
                                                   active_days_last_30, feature_usage_count, 
                                                   last_engagement, engagement_trend)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        engagement_score = EXCLUDED.engagement_score,
                        segment = EXCLUDED.segment,
                        active_days_last_30 = EXCLUDED.active_days_last_30,
                        feature_usage_count = EXCLUDED.feature_usage_count,
                        last_engagement = EXCLUDED.last_engagement,
                        engagement_trend = EXCLUDED.engagement_trend
                """, (customer_id, engagement_score, segment, active_days_30, event_count, 
                      last_event, trend))
            
            # Revenue Features
            cur.execute("""
                SELECT
                    COALESCE(SUM(t.amount), 0)::DECIMAL as total_revenue,
                    COALESCE(AVG(t.amount), 0)::DECIMAL as avg_order,
                    t.subscription_plan
                FROM transactions t
                WHERE t.customer_id = %s AND t.payment_status = 'completed'
                GROUP BY t.subscription_plan
                ORDER BY total_revenue DESC LIMIT 1
            """, (customer_id,))
            
            rev = cur.fetchone()
            if rev and rev[0] and rev[0] > 0:
                total_revenue, avg_order, plan = rev
                mrr = total_revenue / 12
                
                cur.execute("""
                    INSERT INTO feature_revenue (customer_id, total_revenue, avg_order_value,
                                               subscription_plan, mrr, arr)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        total_revenue = EXCLUDED.total_revenue,
                        avg_order_value = EXCLUDED.avg_order_value,
                        subscription_plan = EXCLUDED.subscription_plan,
                        mrr = EXCLUDED.mrr,
                        arr = EXCLUDED.arr
                """, (customer_id, total_revenue, avg_order, plan, mrr, total_revenue))
            
            # Support Features
            cur.execute("""
                SELECT
                    COALESCE(COUNT(st.ticket_id), 0)::INT as total_tickets,
                    COALESCE(AVG(st.resolution_time_hours), 0)::DECIMAL as avg_resolution,
                    COALESCE(AVG(st.satisfaction_score), 0)::DECIMAL as avg_satisfaction
                FROM support_tickets st
                WHERE st.customer_id = %s
            """, (customer_id,))
            
            sup = cur.fetchone()
            if sup:
                total_tickets, avg_resolution, avg_satisfaction = sup
                support_tier = 'Premium' if total_tickets > 5 else ('Standard' if total_tickets > 0 else 'Basic')
                
                cur.execute("""
                    INSERT INTO feature_support (customer_id, total_tickets, avg_resolution_time,
                                               satisfaction_score, support_tier)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        total_tickets = EXCLUDED.total_tickets,
                        avg_resolution_time = EXCLUDED.avg_resolution_time,
                        satisfaction_score = EXCLUDED.satisfaction_score,
                        support_tier = EXCLUDED.support_tier
                """, (customer_id, total_tickets or 0, avg_resolution or 0, 
                      avg_satisfaction or 0, support_tier))
            
            # Churn Risk
            cur.execute("""
                SELECT
                    COALESCE(COUNT(DISTINCT DATE(e.event_timestamp)), 0)::INT as recent_active_days
                FROM events e
                WHERE e.customer_id = %s AND e.event_timestamp > NOW() - INTERVAL '30 days'
            """, (customer_id,))
            
            recent = cur.fetchone()
            recent_days = recent[0] if recent else 0
            churn_score = max(0, min(100, 100 - (recent_days * 3)))
            
            if churn_score >= 70:
                risk_level = 'HIGH'
            elif churn_score >= 40:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            cur.execute("""
                INSERT INTO feature_churn_risk (customer_id, churn_risk_score, 
                                              churn_risk_category, risk_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    churn_risk_score = EXCLUDED.churn_risk_score,
                    risk_level = EXCLUDED.risk_level
            """, (customer_id, churn_score, 'churn', risk_level))
            
            conn.commit()
        
        print(f"[Seed] Populated feature tables for {len(customers)} customers")
    except Exception as e:
        print(f"[Error] Failed to populate features: {e}")
        conn.rollback()

def seed_database():
    """Main seeding function"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        print("[Seed] Starting database seeding from CSV files...")
        
        # Seed raw data tables
        seed_customers(conn)
        seed_transactions(conn)
        seed_support_tickets(conn)
        seed_events(conn)
        
        # Create feature tables
        create_feature_tables(conn)
        
        # Populate feature tables from raw data
        populate_features_from_raw_data(conn)
        
        # Final verification
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers")
        cust_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM feature_engagement")
        eng_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM feature_churn_risk")
        churn_count = cur.fetchone()[0]
        
        print(f"\n[Seed] ✓ Database seeding complete!")
        print(f"       Customers: {cust_count}")
        print(f"       Engagement records: {eng_count}")
        print(f"       Churn records: {churn_count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[Error] Seeding failed: {e}")
        return False

if __name__ == '__main__':
    success = seed_database()
    sys.exit(0 if success else 1)
