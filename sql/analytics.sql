-- ==================== COHORT ANALYSIS & RETENTION ====================

-- Cohort Analysis: Month-over-month retention by signup cohort
WITH monthly_activity AS (
    SELECT
        c.customer_id,
        c.signup_date,
        DATE_TRUNC('month', e.event_timestamp)::DATE as activity_month,
        COUNT(DISTINCT e.event_id) as event_count
    FROM dim_customer c
    LEFT JOIN fact_events e ON c.customer_key = e.customer_key
    WHERE e.event_timestamp IS NOT NULL
    GROUP BY c.customer_id, c.signup_date, DATE_TRUNC('month', e.event_timestamp)::DATE
),
signup_cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', signup_date)::DATE as signup_month,
        activity_month,
        EXTRACT(MONTH FROM AGE(activity_month, DATE_TRUNC('month', signup_date)::DATE)) as months_since_signup,
        event_count
    FROM monthly_activity
    WHERE activity_month IS NOT NULL
),
cohort_data AS (
    SELECT
        signup_month,
        months_since_signup,
        COUNT(DISTINCT customer_id) as customers_active
    FROM signup_cohorts
    GROUP BY signup_month, months_since_signup
),
cohort_sizes AS (
    SELECT
        signup_month,
        customers_active as cohort_size
    FROM cohort_data
    WHERE months_since_signup = 0
)
SELECT
    cd.signup_month,
    cd.months_since_signup,
    cd.customers_active,
    cs.cohort_size,
    ROUND(100.0 * cd.customers_active / cs.cohort_size, 2) as retention_rate
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.signup_month = cs.signup_month
WHERE cd.months_since_signup <= 12
ORDER BY cd.signup_month, cd.months_since_signup;

-- ==================== CHURN ANALYSIS ====================

-- Customers who churned (no activity for 30+ days)
WITH last_activity AS (
    SELECT
        c.customer_key,
        c.customer_id,
        MAX(e.event_timestamp) as last_event_date,
        CURRENT_DATE - MAX(e.event_timestamp)::DATE as days_since_last_activity
    FROM dim_customer c
    LEFT JOIN fact_events e ON c.customer_key = e.customer_key
    WHERE c.is_active = TRUE
    GROUP BY c.customer_key, c.customer_id
)
SELECT
    customer_id,
    last_event_date,
    days_since_last_activity,
    CASE 
        WHEN days_since_last_activity >= 30 THEN 'CHURNED'
        WHEN days_since_last_activity >= 14 THEN 'AT_RISK'
        ELSE 'ACTIVE'
    END as churn_status
FROM last_activity
ORDER BY days_since_last_activity DESC;

-- ==================== USAGE FUNNEL ANALYSIS ====================

-- Event type progression (conversion funnel)
WITH event_rankings AS (
    SELECT
        customer_id,
        event_type,
        event_timestamp,
        ROW_NUMBER() OVER (PARTITION BY customer_id, event_type ORDER BY event_timestamp) as event_sequence
    FROM fact_events
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '90 days'
),
funnel_steps AS (
    SELECT
        'login' as step_name,
        COUNT(DISTINCT customer_id) as customers
    FROM event_rankings
    WHERE event_type = 'login'
    UNION ALL
    SELECT
        'feature_usage' as step_name,
        COUNT(DISTINCT customer_id) as customers
    FROM event_rankings
    WHERE event_type = 'feature_usage'
    UNION ALL
    SELECT
        'upgrade' as step_name,
        COUNT(DISTINCT customer_id) as customers
    FROM event_rankings
    WHERE event_type = 'upgrade'
)
SELECT
    step_name,
    customers,
    ROUND(100.0 * customers / LAG(customers) OVER (ORDER BY customers DESC), 2) as conversion_rate
FROM funnel_steps
ORDER BY customers DESC;

-- ==================== FREQUENCY, RECENCY, MONETARY (RFM) ====================

-- RFM Score for segmentation
WITH rfm_metrics AS (
    SELECT
        c.customer_key,
        c.customer_id,
        c.email,
        -- Recency: days since last activity
        CURRENT_DATE - MAX(e.event_timestamp)::DATE as recency_days,
        -- Frequency: total interactions in last 90 days
        COUNT(DISTINCT e.event_id) as frequency_90d,
        -- Monetary: total revenue
        COALESCE(SUM(t.amount), 0) as monetary_value
    FROM dim_customer c
    LEFT JOIN fact_events e ON c.customer_key = e.customer_key AND e.event_timestamp >= CURRENT_DATE - INTERVAL '90 days'
    LEFT JOIN fact_transactions t ON c.customer_key = t.customer_key
    WHERE c.is_active = TRUE
    GROUP BY c.customer_key, c.customer_id, c.email
),
rfm_scores AS (
    SELECT
        *,
        -- Create quintile scores (1-5) for each metric
        NTILE(5) OVER (ORDER BY recency_days DESC) as r_score,
        NTILE(5) OVER (ORDER BY frequency_90d) as f_score,
        NTILE(5) OVER (ORDER BY monetary_value) as m_score
    FROM rfm_metrics
),
rfm_segments AS (
    SELECT
        customer_id,
        email,
        recency_days,
        frequency_90d,
        monetary_value,
        CONCAT(r_score, f_score, m_score) as rfm_cell,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 2 THEN 'Potential Loyalists'
            WHEN r_score <= 2 AND m_score >= 3 THEN 'At Risk'
            WHEN r_score <= 1 THEN 'Lost'
            ELSE 'Need Attention'
        END as segment
    FROM rfm_scores
)
SELECT * FROM rfm_segments
ORDER BY segment, monetary_value DESC;

-- ==================== MONTHLY REVENUE TREND ====================

SELECT
    DATE_TRUNC('month', t.transaction_timestamp)::DATE as month,
    COUNT(DISTINCT t.transaction_id) as transaction_count,
    SUM(t.amount) as total_revenue,
    COUNT(DISTINCT t.customer_key) as unique_customers,
    AVG(t.amount) as avg_transaction_value
FROM fact_transactions t
GROUP BY DATE_TRUNC('month', t.transaction_timestamp)::DATE
ORDER BY month DESC;

-- ==================== CUSTOMER LIFETIME VALUE (CLV) ====================

-- Predicted CLV based on historical data
WITH customer_history AS (
    SELECT
        c.customer_key,
        c.customer_id,
        c.signup_date,
        EXTRACT(DAY FROM CURRENT_DATE - c.signup_date) as days_as_customer,
        COALESCE(SUM(t.amount), 0) as total_historical_revenue,
        COUNT(DISTINCT t.transaction_id) as total_transactions,
        COALESCE(AVG(t.amount), 0) as avg_transaction_value
    FROM dim_customer c
    LEFT JOIN fact_transactions t ON c.customer_key = t.customer_key
    WHERE c.is_active = TRUE
    GROUP BY c.customer_key, c.customer_id, c.signup_date
)
SELECT
    customer_id,
    days_as_customer,
    total_historical_revenue,
    total_transactions,
    avg_transaction_value,
    -- Simple CLV projection: (avg monthly value) * (expected customer lifetime in months)
    ROUND((total_historical_revenue / NULLIF(days_as_customer, 0) * 30) * 36, 2) as predicted_clv_36m,
    ROUND((total_historical_revenue / NULLIF(days_as_customer, 0) * 30) * 60, 2) as predicted_clv_60m
FROM customer_history
WHERE days_as_customer > 30  -- Exclude very new customers
ORDER BY predicted_clv_60m DESC;
