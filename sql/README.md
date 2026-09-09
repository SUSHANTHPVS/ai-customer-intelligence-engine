# SQL Directory

This directory contains all SQL scripts for data warehouse setup and analytics.

## Files

### `schema.sql`
Complete SQL Data Warehouse schema including:
- **Dimension Tables**: dim_date, dim_customer, dim_product, dim_campaign
- **Fact Tables**: fact_events, fact_transactions, fact_support, fact_marketing
- **Materialized Views**: Performance-optimized views for common queries
- **Indexes**: Query optimization indexes

### `analytics.sql`
Advanced SQL analytics queries including:
- **Cohort Analysis**: Month-over-month retention by signup cohort
- **Churn Analysis**: Identify churned/at-risk customers
- **Funnel Analysis**: Event conversion funnel
- **RFM Segmentation**: Customer segmentation scoring
- **Revenue Trends**: Monthly revenue analysis
- **CLV Calculation**: Customer Lifetime Value projection

### `transformations.sql`
ETL transformations (to be populated with your data pipeline logic)

## Usage

### Setup Database (First Time)
```bash
psql -U postgres -d postgres -f schema.sql
```

### Run Analytics Queries
```bash
psql -U postgres -d customer_intelligence -f analytics.sql
```

### Connect to Database
```bash
psql -U postgres -d customer_intelligence
```

## Key Concepts

### Star Schema
```
                    dim_product
                          |
dim_date ---- fact_events ----
                |      \
          fact_transactions   customer
                |
           fact_support
```

### Dimension Tables (Descriptive)
- **dim_date**: Calendar information
- **dim_customer**: Customer attributes
- **dim_product**: Product catalog
- **dim_campaign**: Marketing campaigns

### Fact Tables (Measurements)
- **fact_events**: User activities
- **fact_transactions**: Revenue transactions
- **fact_support**: Support interactions
- **fact_marketing**: Campaign performance

## Performance Tips

1. **Use Materialized Views** for frequently queried metrics
2. **Partition Fact Tables** by date for large datasets
3. **Index Foreign Keys** (customer_key, date_key)
4. **Use CTEs** for complex logic clarity
5. **Window Functions** for advanced analytics

## Common Queries

### Monthly Revenue
```sql
SELECT DATE_TRUNC('month', transaction_timestamp)::DATE as month,
       SUM(amount) as revenue
FROM fact_transactions
GROUP BY DATE_TRUNC('month', transaction_timestamp)::DATE
ORDER BY month DESC;
```

### Retention by Cohort
```sql
WITH cohorts AS (
    SELECT DATE_TRUNC('month', signup_date)::DATE as signup_month,
           customer_id
    FROM dim_customer
)
SELECT signup_month, COUNT(*) as cohort_size
FROM cohorts
GROUP BY signup_month;
```

### High-Value Customers
```sql
SELECT customer_id, SUM(amount) as total_value
FROM fact_transactions
GROUP BY customer_id
ORDER BY total_value DESC
LIMIT 100;
```

## Next Steps

1. Load synthetic data via Python data generation pipeline
2. Run schema.sql to create tables
3. Execute analytics.sql for initial metrics
4. Refresh materialized views regularly (daily/weekly)
5. Add partition maintenance jobs for scalability
