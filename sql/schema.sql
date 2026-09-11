-- ==================== DATABASE SETUP ====================
-- Create database
CREATE DATABASE IF NOT EXISTS customer_intelligence;

-- ==================== SCHEMA DEFINITION ====================
-- Switch to database
\c customer_intelligence;

-- ==================== RAW FACT TABLES (Phase 2 - Direct from CSV) ====================

-- Customer Dimension
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(100),
    industry VARCHAR(100),
    acquisition_channel VARCHAR(100),
    signup_date TIMESTAMP
);

-- Customer Events (Raw - ~1M rows)
CREATE TABLE events (
    event_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(100),
    feature VARCHAR(100),
    event_timestamp TIMESTAMP,
    session_duration_seconds INTEGER,
    event_value DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Transactions
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50),
    subscription_plan VARCHAR(100),
    amount DECIMAL(12,2),
    currency VARCHAR(10),
    payment_method VARCHAR(100),
    payment_status VARCHAR(50),
    transaction_timestamp TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Support Tickets
CREATE TABLE support_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(50),
    resolution_time_hours DECIMAL(8,2),
    satisfaction_score INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- ==================== INDEXES FOR PERFORMANCE ====================

-- Customer indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_customers_industry ON customers(industry);

-- Events indexes
CREATE INDEX idx_events_customer_id ON events(customer_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_feature ON events(feature);
CREATE INDEX idx_events_timestamp ON events(event_timestamp);

-- Transactions indexes
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_transactions_plan ON transactions(subscription_plan);

-- Support indexes
CREATE INDEX idx_support_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_priority ON support_tickets(priority);
CREATE INDEX idx_support_category ON support_tickets(category);
CREATE INDEX idx_support_created ON support_tickets(created_at);

-- ==================== MATERIALIZED VIEWS FOR ANALYTICS ====================

-- Customer Summary Metrics
CREATE MATERIALIZED VIEW v_customer_summary AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    c.industry,
    c.acquisition_channel,
    c.signup_date,
    COUNT(DISTINCT e.event_id) as total_events,
    COUNT(DISTINCT e.event_type) as unique_event_types,
    COALESCE(SUM(e.session_duration_seconds), 0) as total_session_seconds,
    COUNT(DISTINCT t.transaction_id) as total_transactions,
    COALESCE(SUM(t.amount), 0) as total_revenue,
    MAX(e.event_timestamp) as last_event_date,
    MAX(t.transaction_timestamp) as last_transaction_date,
    COUNT(DISTINCT s.ticket_id) as total_support_tickets
FROM customers c
LEFT JOIN events e ON c.customer_id = e.customer_id
LEFT JOIN transactions t ON c.customer_id = t.customer_id
LEFT JOIN support_tickets s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.country, 
         c.industry, c.acquisition_channel, c.signup_date;

CREATE INDEX idx_v_customer_summary_customer_id ON v_customer_summary(customer_id);
CREATE INDEX idx_v_customer_summary_country ON v_customer_summary(country);

-- Event Aggregation by Date and Type
CREATE MATERIALIZED VIEW v_events_daily AS
SELECT 
    DATE(event_timestamp) as event_date,
    event_type,
    feature,
    COUNT(*) as event_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    AVG(session_duration_seconds) as avg_session_seconds,
    AVG(event_value) as avg_event_value
FROM events
GROUP BY DATE(event_timestamp), event_type, feature;

CREATE INDEX idx_v_events_daily_date ON v_events_daily(event_date);

-- Revenue Analytics
CREATE MATERIALIZED VIEW v_revenue_analytics AS
SELECT 
    DATE(t.transaction_timestamp) as transaction_date,
    t.subscription_plan,
    t.transaction_type,
    t.payment_status,
    COUNT(*) as transaction_count,
    SUM(t.amount) as total_amount,
    AVG(t.amount) as avg_amount,
    COUNT(DISTINCT t.customer_id) as unique_customers
FROM transactions t
GROUP BY DATE(t.transaction_timestamp), t.subscription_plan, 
         t.transaction_type, t.payment_status;

CREATE INDEX idx_v_revenue_analytics_date ON v_revenue_analytics(transaction_date);

-- Support Ticket Analytics
CREATE MATERIALIZED VIEW v_support_analytics AS
SELECT 
    DATE(s.created_at) as ticket_date,
    s.category,
    s.priority,
    COUNT(*) as ticket_count,
    AVG(s.resolution_time_hours) as avg_resolution_hours,
    AVG(s.satisfaction_score) as avg_satisfaction_score,
    COUNT(DISTINCT s.customer_id) as unique_customers
FROM support_tickets s
GROUP BY DATE(s.created_at), s.category, s.priority;

CREATE INDEX idx_v_support_analytics_date ON v_support_analytics(ticket_date);

-- ==================== PERMISSIONS ====================
-- Uncomment and customize as needed:
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_role;
-- GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO analyst_role;
