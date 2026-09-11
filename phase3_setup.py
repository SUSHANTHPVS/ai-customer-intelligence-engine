#!/usr/bin/env python3
"""
Phase 3: Feature Engineering & ML Pipeline Setup
Purpose: Transform raw event data into ML-ready features for customer intelligence
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3FeatureEngineering:
    """Phase 3: Feature Engineering from raw customer event data"""
    
    def __init__(self, db_host="localhost", db_port=5432, db_user="postgres", 
                 db_password="sushanth123", db_name="customer_intelligence"):
        """Initialize Phase 3 Feature Engineering"""
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.project_root = Path(__file__).parent
        self.conn = None
        self.cursor = None
    
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def close_database(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query, fetch=False):
        """Execute SQL query"""
        try:
            self.cursor.execute(query)
            self.conn.commit()
            if fetch:
                return True, self.cursor.fetchall()
            return True, None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            return False, str(e)
    
    def create_feature_tables(self):
        """Create tables for engineered features"""
        print("\n[1/7] Creating feature tables...")
        
        queries = [
            # RFM Features (Recency, Frequency, Monetary)
            """
            CREATE TABLE IF NOT EXISTS feature_rfm (
                customer_id VARCHAR(50) PRIMARY KEY,
                recency_days INTEGER,
                frequency_transactions INTEGER,
                monetary_value DECIMAL(12,2),
                rfm_score DECIMAL(5,2),
                rfm_segment VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Behavioral Features
            """
            CREATE TABLE IF NOT EXISTS feature_behavioral (
                customer_id VARCHAR(50) PRIMARY KEY,
                total_events INTEGER,
                unique_event_types INTEGER,
                unique_features_used INTEGER,
                avg_session_duration DECIMAL(10,2),
                total_session_time DECIMAL(12,2),
                login_frequency INTEGER,
                feature_usage_premium_pct DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """,
            
            # Engagement Features
            """
            CREATE TABLE IF NOT EXISTS feature_engagement (
                customer_id VARCHAR(50) PRIMARY KEY,
                engagement_score NUMERIC(10,2),
                days_since_signup INTEGER,
                days_active INTEGER,
                activity_trend VARCHAR(50),
                is_active_last_30days BOOLEAN,
                is_active_last_7days BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """,
            
            # Revenue Features
            """
            CREATE TABLE IF NOT EXISTS feature_revenue (
                customer_id VARCHAR(50) PRIMARY KEY,
                total_revenue DECIMAL(12,2),
                subscription_plan VARCHAR(100),
                avg_transaction_value DECIMAL(12,2),
                transaction_frequency DECIMAL(5,2),
                payment_method_preferred VARCHAR(100),
                failed_payment_count INTEGER,
                subscription_tenure_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """,
            
            # Support Features
            """
            CREATE TABLE IF NOT EXISTS feature_support (
                customer_id VARCHAR(50) PRIMARY KEY,
                total_tickets INTEGER,
                avg_resolution_hours DECIMAL(8,2),
                avg_satisfaction_score DECIMAL(5,2),
                critical_priority_count INTEGER,
                support_category_preference VARCHAR(100),
                issue_resolution_rate DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """,
            
            # Churn Risk Features
            """
            CREATE TABLE IF NOT EXISTS feature_churn_risk (
                customer_id VARCHAR(50) PRIMARY KEY,
                churn_risk_score DECIMAL(5,2),
                churn_risk_category VARCHAR(50),
                days_inactive INTEGER,
                declining_engagement BOOLEAN,
                high_support_tickets BOOLEAN,
                failed_payments BOOLEAN,
                declining_revenue BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """,
            
            # Master Feature Table (for ML models)
            """
            CREATE TABLE IF NOT EXISTS feature_master (
                customer_id VARCHAR(50) PRIMARY KEY,
                country VARCHAR(100),
                industry VARCHAR(100),
                acquisition_channel VARCHAR(100),
                days_since_signup INTEGER,
                total_events INTEGER,
                total_revenue DECIMAL(12,2),
                total_transactions INTEGER,
                subscription_plan VARCHAR(100),
                engagement_score NUMERIC(10,2),
                churn_risk_score NUMERIC(10,2),
                is_active_last_30days BOOLEAN,
                total_support_tickets INTEGER,
                avg_satisfaction_score DECIMAL(5,2),
                rfm_segment VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        for query in queries:
            success, error = self.execute_query(query)
            if not success:
                print(f"      ERROR creating feature table: {error}")
                return False
        
        print("      OK - Feature tables created (6 tables)")
        return True
    
    def calculate_rfm_features(self):
        """Calculate RFM (Recency, Frequency, Monetary) features"""
        print("\n[2/6] Calculating RFM features...")
        
        query = """
        INSERT INTO feature_rfm (customer_id, recency_days, frequency_transactions, monetary_value, rfm_score, rfm_segment)
        SELECT 
            c.customer_id,
            COALESCE(
                EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(t.transaction_timestamp)))::INTEGER,
                999
            ) as recency_days,
            COUNT(t.transaction_id)::INTEGER as frequency_transactions,
            COALESCE(SUM(t.amount), 0) as monetary_value,
            COALESCE(
                LEAST(100, GREATEST(0,
                    (5 - LEAST(5, (EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(t.transaction_timestamp))) / 60.0))) +
                    LEAST(5, (COUNT(t.transaction_id)::DECIMAL / 100)) +
                    LEAST(5, (COALESCE(SUM(t.amount), 0) / 100000))
                )),
                0
            )::NUMERIC(10,2) as rfm_score,
            CASE 
                WHEN COUNT(t.transaction_id) >= 10 AND SUM(t.amount) >= 5000 THEN 'HIGH_VALUE'
                WHEN COUNT(t.transaction_id) >= 5 AND SUM(t.amount) >= 2000 THEN 'MEDIUM_VALUE'
                WHEN EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(t.transaction_timestamp))) <= 30 THEN 'ACTIVE'
                WHEN EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(t.transaction_timestamp))) <= 90 THEN 'AT_RISK'
                ELSE 'DORMANT'
            END as rfm_segment
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.customer_id
        ON CONFLICT (customer_id) DO UPDATE SET
            recency_days = EXCLUDED.recency_days,
            frequency_transactions = EXCLUDED.frequency_transactions,
            monetary_value = EXCLUDED.monetary_value,
            rfm_score = EXCLUDED.rfm_score,
            rfm_segment = EXCLUDED.rfm_segment;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - RFM features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def calculate_behavioral_features(self):
        """Calculate behavioral engagement features"""
        print("\n[3/6] Calculating behavioral features...")
        
        query = """
        INSERT INTO feature_behavioral (customer_id, total_events, unique_event_types, unique_features_used, 
                                        avg_session_duration, total_session_time, login_frequency, 
                                        feature_usage_premium_pct)
        SELECT 
            c.customer_id,
            COUNT(e.event_id)::INTEGER as total_events,
            COUNT(DISTINCT e.event_type)::INTEGER as unique_event_types,
            COUNT(DISTINCT e.feature)::INTEGER as unique_features_used,
            COALESCE(AVG(e.session_duration_seconds), 0)::DECIMAL(10,2) as avg_session_duration,
            COALESCE(SUM(e.session_duration_seconds), 0)::DECIMAL(12,2) as total_session_time,
            COUNT(CASE WHEN e.event_type = 'login' THEN 1 END)::INTEGER as login_frequency,
            COALESCE(
                (COUNT(CASE WHEN e.feature = 'premium_feature' THEN 1 END)::DECIMAL / 
                 NULLIF(COUNT(e.event_id), 0) * 100),
                0
            )::DECIMAL(5,2) as feature_usage_premium_pct
        FROM customers c
        LEFT JOIN events e ON c.customer_id = e.customer_id
        GROUP BY c.customer_id
        ON CONFLICT (customer_id) DO UPDATE SET
            total_events = EXCLUDED.total_events,
            unique_event_types = EXCLUDED.unique_event_types,
            unique_features_used = EXCLUDED.unique_features_used,
            avg_session_duration = EXCLUDED.avg_session_duration,
            total_session_time = EXCLUDED.total_session_time,
            login_frequency = EXCLUDED.login_frequency,
            feature_usage_premium_pct = EXCLUDED.feature_usage_premium_pct;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - Behavioral features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def calculate_engagement_features(self):
        """Calculate engagement and activity features"""
        print("\n[4/6] Calculating engagement features...")
        
        query = """
        INSERT INTO feature_engagement (customer_id, engagement_score, days_since_signup, days_active, 
                                        activity_trend, is_active_last_30days, is_active_last_7days)
        SELECT 
            c.customer_id,
            COALESCE(
                LEAST(100,
                    ((COUNT(DISTINCT DATE(e.event_timestamp))::DECIMAL / 365) * 40 +
                     ((COUNT(e.event_id)::DECIMAL / 500) * 35) +
                     ((COALESCE(SUM(t.amount), 0)::DECIMAL / 1000) * 25))
                ),
                0
            )::NUMERIC(10,2) as engagement_score,
            EXTRACT(DAY FROM (CURRENT_TIMESTAMP - c.signup_date))::INTEGER as days_since_signup,
            COUNT(DISTINCT DATE(e.event_timestamp))::INTEGER as days_active,
            CASE 
                WHEN MAX(e.event_timestamp) >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'ACTIVE'
                WHEN MAX(e.event_timestamp) >= CURRENT_TIMESTAMP - INTERVAL '90 days' THEN 'INACTIVE_30'
                ELSE 'DORMANT'
            END as activity_trend,
            MAX(e.event_timestamp) >= CURRENT_TIMESTAMP - INTERVAL '30 days' as is_active_last_30days,
            MAX(e.event_timestamp) >= CURRENT_TIMESTAMP - INTERVAL '7 days' as is_active_last_7days
        FROM customers c
        LEFT JOIN events e ON c.customer_id = e.customer_id
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.customer_id, c.signup_date
        ON CONFLICT (customer_id) DO UPDATE SET
            engagement_score = EXCLUDED.engagement_score,
            days_since_signup = EXCLUDED.days_since_signup,
            days_active = EXCLUDED.days_active,
            activity_trend = EXCLUDED.activity_trend,
            is_active_last_30days = EXCLUDED.is_active_last_30days,
            is_active_last_7days = EXCLUDED.is_active_last_7days;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - Engagement features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def calculate_revenue_features(self):
        """Calculate revenue and subscription features"""
        print("\n[5/7] Calculating revenue features...")
        
        query = """
        INSERT INTO feature_revenue (customer_id, total_revenue, subscription_plan, avg_transaction_value, 
                                     transaction_frequency, payment_method_preferred, failed_payment_count, 
                                     subscription_tenure_days)
        SELECT 
            c.customer_id,
            COALESCE(SUM(t.amount), 0)::DECIMAL(12,2) as total_revenue,
            (SELECT subscription_plan FROM transactions WHERE customer_id = c.customer_id 
             GROUP BY subscription_plan ORDER BY COUNT(*) DESC LIMIT 1) as subscription_plan,
            COALESCE(AVG(t.amount), 0)::DECIMAL(12,2) as avg_transaction_value,
            COALESCE((COUNT(t.transaction_id)::DECIMAL / NULLIF(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MIN(t.transaction_timestamp))), 0) * 30), 0)::NUMERIC(10,2) as transaction_frequency,
            (SELECT payment_method FROM transactions WHERE customer_id = c.customer_id 
             GROUP BY payment_method ORDER BY COUNT(*) DESC LIMIT 1) as payment_method_preferred,
            COUNT(CASE WHEN t.payment_status = 'failed' THEN 1 END)::INTEGER as failed_payment_count,
            COALESCE(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MIN(t.transaction_timestamp)))::INTEGER, 0) as subscription_tenure_days
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.customer_id
        ON CONFLICT (customer_id) DO UPDATE SET
            total_revenue = EXCLUDED.total_revenue,
            subscription_plan = EXCLUDED.subscription_plan,
            avg_transaction_value = EXCLUDED.avg_transaction_value,
            transaction_frequency = EXCLUDED.transaction_frequency,
            payment_method_preferred = EXCLUDED.payment_method_preferred,
            failed_payment_count = EXCLUDED.failed_payment_count,
            subscription_tenure_days = EXCLUDED.subscription_tenure_days;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - Revenue features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def calculate_support_features(self):
        """Calculate support ticket features"""
        print("\n[6/7] Calculating support features...")
        
        query = """
        INSERT INTO feature_support (customer_id, total_tickets, avg_resolution_hours, avg_satisfaction_score, 
                                     critical_priority_count, support_category_preference, issue_resolution_rate)
        SELECT 
            c.customer_id,
            COUNT(st.ticket_id)::INTEGER as total_tickets,
            COALESCE(AVG(st.resolution_time_hours), 0)::DECIMAL(8,2) as avg_resolution_hours,
            COALESCE(AVG(st.satisfaction_score), 0)::DECIMAL(5,2) as avg_satisfaction_score,
            COUNT(CASE WHEN st.priority = 'critical' THEN 1 END)::INTEGER as critical_priority_count,
            (SELECT category FROM support_tickets WHERE customer_id = c.customer_id 
             GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1) as support_category_preference,
            COALESCE(
                (COUNT(CASE WHEN st.satisfaction_score >= 3 THEN 1 END)::DECIMAL / 
                 NULLIF(COUNT(st.ticket_id), 0) * 100),
                0
            )::DECIMAL(5,2) as issue_resolution_rate
        FROM customers c
        LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
        GROUP BY c.customer_id
        ON CONFLICT (customer_id) DO UPDATE SET
            total_tickets = EXCLUDED.total_tickets,
            avg_resolution_hours = EXCLUDED.avg_resolution_hours,
            avg_satisfaction_score = EXCLUDED.avg_satisfaction_score,
            critical_priority_count = EXCLUDED.critical_priority_count,
            support_category_preference = EXCLUDED.support_category_preference,
            issue_resolution_rate = EXCLUDED.issue_resolution_rate;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - Support features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def calculate_churn_risk_features(self):
        """Calculate churn risk indicators"""
        print("\n[7/7] Calculating churn risk features...")
        
        query = """
        INSERT INTO feature_churn_risk (customer_id, churn_risk_score, churn_risk_category, days_inactive, 
                                        declining_engagement, high_support_tickets, failed_payments, 
                                        declining_revenue)
        SELECT 
            c.customer_id,
            COALESCE(
                LEAST(100,
                    ((EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(MAX(e.event_timestamp), c.signup_date))) / 365.0) * 40 +
                     (CASE WHEN COUNT(CASE WHEN s.ticket_id IS NOT NULL THEN 1 END) > 5 THEN 25 ELSE 0 END) +
                     (CASE WHEN COUNT(CASE WHEN t.payment_status = 'failed' THEN 1 END) > 0 THEN 20 ELSE 0 END) +
                     (CASE WHEN AVG(COALESCE(s.satisfaction_score, 3)) < 3 THEN 15 ELSE 0 END))
                ),
                0
            )::NUMERIC(10,2) as churn_risk_score,
            CASE 
                WHEN ((EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(MAX(e.event_timestamp), c.signup_date))) / 365.0) * 40 +
                      (CASE WHEN COUNT(CASE WHEN s.ticket_id IS NOT NULL THEN 1 END) > 5 THEN 25 ELSE 0 END) +
                      (CASE WHEN COUNT(CASE WHEN t.payment_status = 'failed' THEN 1 END) > 0 THEN 20 ELSE 0 END)) >= 70 THEN 'CRITICAL'
                WHEN ((EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(MAX(e.event_timestamp), c.signup_date))) / 365.0) * 40 +
                      (CASE WHEN COUNT(CASE WHEN s.ticket_id IS NOT NULL THEN 1 END) > 5 THEN 25 ELSE 0 END)) >= 40 THEN 'HIGH'
                WHEN ((EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(MAX(e.event_timestamp), c.signup_date))) / 365.0) * 40) >= 20 THEN 'MEDIUM'
                ELSE 'LOW'
            END as churn_risk_category,
            EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(MAX(e.event_timestamp), c.signup_date)))::INTEGER as days_inactive,
            COUNT(e.event_id) < 10 as declining_engagement,
            COUNT(CASE WHEN s.ticket_id IS NOT NULL THEN 1 END) > 5 as high_support_tickets,
            COUNT(CASE WHEN t.payment_status = 'failed' THEN 1 END) > 0 as failed_payments,
            FALSE as declining_revenue
        FROM customers c
        LEFT JOIN events e ON c.customer_id = e.customer_id
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        LEFT JOIN support_tickets s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.signup_date
        ON CONFLICT (customer_id) DO UPDATE SET
            churn_risk_score = EXCLUDED.churn_risk_score,
            churn_risk_category = EXCLUDED.churn_risk_category,
            days_inactive = EXCLUDED.days_inactive,
            declining_engagement = EXCLUDED.declining_engagement,
            high_support_tickets = EXCLUDED.high_support_tickets,
            failed_payments = EXCLUDED.failed_payments;
        """
        
        success, error = self.execute_query(query)
        if success:
            print("      OK - Churn risk features calculated")
            return True
        else:
            print(f"      ERROR: {error}")
            return False
    
    def run_phase3_setup(self):
        """Run complete Phase 3 setup"""
        print("\n" + "=" * 70)
        print("PHASE 3: Feature Engineering & ML Pipeline Setup")
        print("=" * 70)
        print(f"Target: {self.db_name} @ {self.db_host}:{self.db_port}")
        
        # Connect to database
        if not self.connect_database():
            print("ERROR: Failed to connect to database")
            return False
        
        # Run feature engineering steps
        steps = [
            self.create_feature_tables,
            self.calculate_rfm_features,
            self.calculate_behavioral_features,
            self.calculate_engagement_features,
            self.calculate_revenue_features,
            self.calculate_support_features,
            self.calculate_churn_risk_features,
        ]
        
        success_count = 0
        for step in steps:
            try:
                if step():
                    success_count += 1
                else:
                    print(f"\n*** Feature Engineering step failed ***")
                    break
            except Exception as e:
                print(f"\n*** Unexpected error: {e} ***")
                break
        
        # Close connection
        self.close_database()
        
        # Print summary
        print("\n" + "=" * 70)
        if success_count == len(steps):
            print("✅ SUCCESS - Phase 3 Feature Engineering Complete!")
            print("\nFeature Tables Created:")
            print("  ✓ feature_rfm (RFM segmentation)")
            print("  ✓ feature_behavioral (Event engagement)")
            print("  ✓ feature_engagement (Activity metrics)")
            print("  ✓ feature_revenue (Subscription & payment)")
            print("  ✓ feature_support (Support tickets)")
            print("  ✓ feature_churn_risk (Churn prediction)")
            print("\nNext Steps:")
            print("  1. Review features with: SELECT * FROM feature_rfm LIMIT 10;")
            print("  2. Create feature_master table combining all features")
            print("  3. Build ML models for churn prediction")
            print("  4. Deploy prediction API")
        else:
            print(f"PARTIAL - Completed {success_count}/7 feature engineering steps")
        print("=" * 70 + "\n")
        
        return success_count == len(steps)


if __name__ == "__main__":
    import os
    
    # Get password from environment or use default
    db_password = os.environ.get('PGPASSWORD', 'sushanth123')
    
    phase3 = Phase3FeatureEngineering(
        db_host="localhost",
        db_port=5432,
        db_user="postgres",
        db_password=db_password,
        db_name="customer_intelligence"
    )
    
    success = phase3.run_phase3_setup()
    sys.exit(0 if success else 1)
