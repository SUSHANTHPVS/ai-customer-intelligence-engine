-- ==================== DATABASE SETUP ====================
-- Create database
CREATE DATABASE customer_intelligence;

-- ==================== SCHEMA DEFINITION ====================
-- Switch to database
\c customer_intelligence;

-- ==================== DIMENSION TABLES ====================

-- Dimension: Date
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date_value DATE UNIQUE NOT NULL,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    day_of_week INTEGER,
    week_of_year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- Dimension: Customer
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    country VARCHAR(100),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    acquisition_channel VARCHAR(100),
    signup_date DATE,
    customer_segment VARCHAR(50),  -- Power User, At-Risk, Dormant, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Product
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    price_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Campaign
CREATE TABLE dim_campaign (
    campaign_key SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE NOT NULL,
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(100),
    channel VARCHAR(100),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== FACT TABLES ====================

-- Fact: Customer Events
CREATE TABLE fact_events (
    event_key SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL,
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    event_type VARCHAR(100),  -- login, feature_usage, page_view, etc.
    session_id VARCHAR(100),
    session_duration_seconds INTEGER,
    event_timestamp TIMESTAMP,
    event_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Transactions
CREATE TABLE fact_transactions (
    transaction_key SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    transaction_type VARCHAR(50),  -- subscription, upgrade, downgrade, refund
    subscription_plan VARCHAR(100),
    amount DECIMAL(12,2),
    currency VARCHAR(10),
    payment_method VARCHAR(100),
    payment_status VARCHAR(50),  -- completed, failed, pending
    transaction_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Support Tickets
CREATE TABLE fact_support (
    ticket_key SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    category VARCHAR(100),
    priority VARCHAR(50),  -- low, medium, high, critical
    resolution_time_hours DECIMAL(8,2),
    satisfaction_score INTEGER,  -- 1-5 scale
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Fact: Marketing
CREATE TABLE fact_marketing (
    marketing_key SERIAL PRIMARY KEY,
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    campaign_key INTEGER NOT NULL REFERENCES dim_campaign(campaign_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    cost DECIMAL(12,2),
    revenue DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== INDEXES ====================

CREATE INDEX idx_customer_email ON dim_customer(email);
CREATE INDEX idx_customer_country ON dim_customer(country);
CREATE INDEX idx_customer_segment ON dim_customer(customer_segment);

CREATE INDEX idx_events_customer_key ON fact_events(customer_key);
CREATE INDEX idx_events_date_key ON fact_events(date_key);
CREATE INDEX idx_events_event_type ON fact_events(event_type);
CREATE INDEX idx_events_timestamp ON fact_events(event_timestamp);

CREATE INDEX idx_transactions_customer_key ON fact_transactions(customer_key);
CREATE INDEX idx_transactions_date_key ON fact_transactions(date_key);
CREATE INDEX idx_transactions_type ON fact_transactions(transaction_type);

CREATE INDEX idx_support_customer_key ON fact_support(customer_key);
CREATE INDEX idx_support_priority ON fact_support(priority);

CREATE INDEX idx_marketing_customer_key ON fact_marketing(customer_key);
CREATE INDEX idx_marketing_campaign_key ON fact_marketing(campaign_key);

-- ==================== MATERIALIZED VIEWS FOR PERFORMANCE ====================

-- Customer Metrics (updated daily)
CREATE MATERIALIZED VIEW v_customer_metrics AS
SELECT
    c.customer_key,
    c.customer_id,
    COUNT(DISTINCT e.event_id) as total_events,
    COUNT(DISTINCT e.session_id) as total_sessions,
    SUM(e.session_duration_seconds) as total_session_minutes,
    COUNT(DISTINCT t.transaction_id) as total_transactions,
    SUM(t.amount) as total_revenue,
    MAX(e.event_timestamp) as last_event_timestamp,
    MAX(t.transaction_timestamp) as last_transaction_timestamp,
    COUNT(DISTINCT s.ticket_id) as total_support_tickets
FROM dim_customer c
LEFT JOIN fact_events e ON c.customer_key = e.customer_key
LEFT JOIN fact_transactions t ON c.customer_key = t.customer_key
LEFT JOIN fact_support s ON c.customer_key = s.customer_key
GROUP BY c.customer_key, c.customer_id;

CREATE INDEX idx_v_customer_metrics_customer_key ON v_customer_metrics(customer_key);

-- ==================== PERMISSIONS ====================
-- (Uncomment and modify as needed for your team)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_role;
-- GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO analyst_role;
