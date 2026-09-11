# 🚀 PHASE 3: Feature Engineering & ML Pipeline

## Overview

Phase 3 transforms raw customer event data into **machine learning-ready features** for:
- ✅ Churn prediction
- ✅ Customer segmentation
- ✅ Revenue forecasting
- ✅ Engagement scoring
- ✅ RFM analysis

---

## 📊 Engineered Feature Tables (6 Tables)

### 1. **feature_rfm** - RFM Segmentation
Recency, Frequency, Monetary analysis for customer value stratification

```sql
SELECT * FROM feature_rfm LIMIT 10;
```

**Columns:**
- `recency_days`: Days since last transaction (lower = more recent)
- `frequency_transactions`: Total transactions (higher = more engaged)
- `monetary_value`: Total revenue (higher = more valuable)
- `rfm_score`: Composite RFM score (0-100)
- `rfm_segment`: HIGH_VALUE | MEDIUM_VALUE | ACTIVE | AT_RISK | DORMANT

**Use Case:** Customer value segmentation, VIP targeting, retention campaigns

---

### 2. **feature_behavioral** - Event Engagement
Behavioral patterns from 1M+ customer events

```sql
SELECT * FROM feature_behavioral LIMIT 10;
```

**Columns:**
- `total_events`: Total events from this customer
- `unique_event_types`: Diverse behaviors (login, feature_usage, page_view, etc.)
- `unique_features_used`: Feature adoption breadth
- `avg_session_duration`: Average session length (seconds)
- `total_session_time`: Total time spent (seconds)
- `login_frequency`: Login count (engagement indicator)
- `feature_usage_premium_pct`: Premium feature usage percentage

**Use Case:** Feature adoption analysis, engagement scoring, UX improvements

---

### 3. **feature_engagement** - Activity & Engagement
Temporal engagement patterns and activity trends

```sql
SELECT * FROM feature_engagement LIMIT 10;
```

**Columns:**
- `engagement_score`: Composite engagement metric (0-100)
- `days_since_signup`: Account age
- `days_active`: Number of active days
- `activity_trend`: ACTIVE | INACTIVE_30 | DORMANT
- `is_active_last_30days`: Boolean activity flag
- `is_active_last_7days`: Recent activity indicator

**Use Case:** Churn detection, re-engagement campaigns, lifecycle tracking

---

### 4. **feature_revenue** - Financial Profile
Subscription and payment patterns

```sql
SELECT * FROM feature_revenue LIMIT 10;
```

**Columns:**
- `total_revenue`: Total customer lifetime value
- `subscription_plan`: Primary subscription (Enterprise, Premium, etc.)
- `avg_transaction_value`: Average purchase amount
- `transaction_frequency`: Transactions per month
- `payment_method_preferred`: Most used payment method
- `failed_payment_count`: Failed transaction count (risk indicator)
- `subscription_tenure_days`: How long subscribed

**Use Case:** Revenue forecasting, payment risk analysis, upsell targeting

---

### 5. **feature_support** - Customer Support Profile
Support interaction patterns and satisfaction

```sql
SELECT * FROM feature_support LIMIT 10;
```

**Columns:**
- `total_tickets`: Support ticket count
- `avg_resolution_hours`: Support efficiency
- `avg_satisfaction_score`: Customer satisfaction (1-5 scale)
- `critical_priority_count`: High-priority issues
- `support_category_preference`: Most common issue type
- `issue_resolution_rate`: Resolution percentage

**Use Case:** Support quality analysis, churn correlation, issue prevention

---

### 6. **feature_churn_risk** - Churn Prediction Indicators
Comprehensive churn risk scoring and categorization

```sql
SELECT * FROM feature_churn_risk LIMIT 10;
```

**Columns:**
- `churn_risk_score`: Composite churn risk (0-100, higher = more risk)
- `churn_risk_category`: CRITICAL | HIGH | MEDIUM | LOW
- `days_inactive`: Days since last activity
- `declining_engagement`: Is engagement dropping?
- `high_support_tickets`: More than 5 tickets? (dissatisfaction indicator)
- `failed_payments`: Payment issues present?
- `declining_revenue`: Revenue trend (calculated separately)

**Use Case:** Churn prediction, proactive retention, intervention prioritization

---

## 🔄 Feature Engineering Pipeline

### Step-by-Step Execution

1. **Create Feature Tables** (6 new tables)
2. **Calculate RFM Features** - From transaction history
3. **Calculate Behavioral Features** - From 1M event records
4. **Calculate Engagement Features** - Activity trends and patterns
5. **Calculate Revenue Features** - Subscription & payment data
6. **Calculate Churn Risk Features** - Risk scoring algorithms

### Run Phase 3 Setup

```powershell
# Navigate to project
cd "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

# Set password
$env:PGPASSWORD='sushanth123'

# Run Phase 3
python phase3_setup.py
```

**Expected Output:**
```
======================================================================
PHASE 3: Feature Engineering & ML Pipeline Setup
======================================================================

[1/6] Creating feature tables...
      OK - Feature tables created (6 tables)

[2/6] Calculating RFM features...
      OK - RFM features calculated

[3/6] Calculating behavioral features...
      OK - Behavioral features calculated

[4/6] Calculating engagement features...
      OK - Engagement features calculated

[5/6] Calculating revenue features...
      OK - Revenue features calculated

[6/6] Calculating churn risk features...
      OK - Churn risk features calculated

✅ SUCCESS - Phase 3 Feature Engineering Complete!
```

---

## 📈 Sample Analytics Queries

### High-Risk Churn Customers

```sql
SELECT 
    c.customer_id,
    c.email,
    c.industry,
    cr.churn_risk_score,
    cr.churn_risk_category,
    cr.days_inactive,
    rf.rfm_segment,
    rv.total_revenue
FROM feature_churn_risk cr
JOIN customers c ON c.customer_id = cr.customer_id
JOIN feature_rfm rf ON rf.customer_id = cr.customer_id
JOIN feature_revenue rv ON rv.customer_id = cr.customer_id
WHERE cr.churn_risk_category IN ('CRITICAL', 'HIGH')
ORDER BY cr.churn_risk_score DESC
LIMIT 100;
```

### High-Value Engaged Customers (Upsell Targets)

```sql
SELECT 
    c.customer_id,
    c.email,
    rf.rfm_score,
    rf.rfm_segment,
    en.engagement_score,
    rv.total_revenue,
    rv.subscription_plan,
    bh.feature_usage_premium_pct
FROM feature_rfm rf
JOIN feature_engagement en ON en.customer_id = rf.customer_id
JOIN feature_revenue rv ON rv.customer_id = rf.customer_id
JOIN feature_behavioral bh ON bh.customer_id = rf.customer_id
JOIN customers c ON c.customer_id = rf.customer_id
WHERE rf.rfm_segment = 'HIGH_VALUE'
  AND en.engagement_score > 70
  AND rv.subscription_plan != 'Enterprise'
ORDER BY rv.total_revenue DESC;
```

### Customers by Engagement Segment

```sql
SELECT 
    en.activity_trend,
    COUNT(*) as customer_count,
    AVG(rv.total_revenue) as avg_revenue,
    AVG(en.engagement_score) as avg_engagement,
    AVG(cr.churn_risk_score) as avg_churn_risk,
    SUM(rv.total_revenue) as total_segment_revenue
FROM feature_engagement en
JOIN feature_revenue rv ON rv.customer_id = en.customer_id
JOIN feature_churn_risk cr ON cr.customer_id = en.customer_id
GROUP BY en.activity_trend
ORDER BY total_segment_revenue DESC;
```

### Support Quality Impact on Churn

```sql
SELECT 
    sp.avg_satisfaction_score,
    COUNT(*) as customer_count,
    AVG(cr.churn_risk_score) as avg_churn_risk,
    COUNT(CASE WHEN cr.churn_risk_category IN ('CRITICAL', 'HIGH') THEN 1 END) as high_risk_count,
    ROUND(100.0 * COUNT(CASE WHEN cr.churn_risk_category IN ('CRITICAL', 'HIGH') THEN 1 END) / 
          COUNT(*), 2) as churn_risk_pct
FROM feature_support sp
JOIN feature_churn_risk cr ON cr.customer_id = sp.customer_id
GROUP BY sp.avg_satisfaction_score
ORDER BY sp.avg_satisfaction_score DESC;
```

### Feature Importance: Premium Feature Usage vs Churn

```sql
SELECT 
    CASE 
        WHEN bh.feature_usage_premium_pct > 50 THEN 'HIGH_PREMIUM_USER'
        WHEN bh.feature_usage_premium_pct > 20 THEN 'MEDIUM_PREMIUM_USER'
        ELSE 'LOW_PREMIUM_USER'
    END as premium_usage_segment,
    COUNT(*) as customer_count,
    AVG(cr.churn_risk_score) as avg_churn_risk,
    AVG(en.engagement_score) as avg_engagement,
    AVG(rv.total_revenue) as avg_revenue
FROM feature_behavioral bh
JOIN feature_churn_risk cr ON cr.customer_id = bh.customer_id
JOIN feature_engagement en ON en.customer_id = bh.customer_id
JOIN feature_revenue rv ON rv.customer_id = bh.customer_id
GROUP BY premium_usage_segment
ORDER BY avg_churn_risk ASC;
```

---

## 🤖 ML Model Use Cases

### 1. Churn Prediction Model
**Target Variable:** `feature_churn_risk.churn_risk_category`  
**Features:** All 6 feature tables  
**Algorithm:** Random Forest / XGBoost  
**Output:** Probability of churn in 30/60/90 days

```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import psycopg2

# Load features
conn = psycopg2.connect(...)
df = pd.read_sql("""
    SELECT 
        c.customer_id,
        c.country,
        rf.rfm_score,
        en.engagement_score,
        rv.total_revenue,
        sp.avg_satisfaction_score,
        cr.churn_risk_score
    FROM feature_rfm rf
    JOIN feature_engagement en ON en.customer_id = rf.customer_id
    JOIN feature_revenue rv ON rv.customer_id = rf.customer_id
    JOIN feature_support sp ON sp.customer_id = rf.customer_id
    JOIN feature_churn_risk cr ON cr.customer_id = rf.customer_id
    JOIN customers c ON c.customer_id = rf.customer_id
""", conn)

# Train model
X = df[['rfm_score', 'engagement_score', 'total_revenue', 'avg_satisfaction_score']]
y = (df['churn_risk_score'] > 50).astype(int)
model = RandomForestClassifier().fit(X, y)
```

### 2. Customer Segmentation Model
**Features:** RFM, Engagement, Revenue  
**Algorithm:** K-Means Clustering  
**Output:** 4-5 customer segments for targeted strategies

### 3. Revenue Forecasting Model
**Target Variable:** Next month's revenue  
**Features:** Historical transaction_value, frequency, plan  
**Algorithm:** Time Series ARIMA or Prophet

### 4. Engagement Prediction Model
**Target Variable:** Will customer be active next month?  
**Features:** Recent activity, login frequency, feature usage  
**Algorithm:** Logistic Regression / Neural Network

---

## 📁 File Structure

```
AI Customer Intelligence Engine/
├── phase3_setup.py              # Phase 3 automation script
├── PHASE3_FEATURES.md           # This file
├── notebooks/
│   ├── feature_analysis.ipynb   # Feature exploration
│   └── churn_modeling.ipynb     # ML model development
├── src/
│   ├── models/
│   │   ├── churn_model.py
│   │   ├── segmentation_model.py
│   │   └── revenue_forecast.py
│   └── utils/
│       └── feature_loader.py
└── data/
    ├── raw/                     # Phase 2 CSV files
    └── features/                # Phase 3 feature exports
```

---

## 🔍 Feature Quality Checks

### Verify Features Are Calculated

```powershell
$env:PGPASSWORD='sushanth123'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -U postgres -d customer_intelligence -c "
SELECT 'feature_rfm' as table_name, COUNT(*) as rows FROM feature_rfm
UNION ALL SELECT 'feature_behavioral', COUNT(*) FROM feature_behavioral
UNION ALL SELECT 'feature_engagement', COUNT(*) FROM feature_engagement
UNION ALL SELECT 'feature_revenue', COUNT(*) FROM feature_revenue
UNION ALL SELECT 'feature_support', COUNT(*) FROM feature_support
UNION ALL SELECT 'feature_churn_risk', COUNT(*) FROM feature_churn_risk;"
```

**Expected:** All tables should have **~10,000 rows** (one per customer)

### Check for Missing Values

```sql
SELECT 
    'rfm_score' as metric,
    COUNT(*) as total_rows,
    COUNT(rfm_score) as non_null,
    ROUND(100.0 * COUNT(rfm_score) / COUNT(*), 2) as completeness_pct
FROM feature_rfm
UNION ALL
SELECT 'engagement_score', COUNT(*), COUNT(engagement_score),
    ROUND(100.0 * COUNT(engagement_score) / COUNT(*), 2)
FROM feature_engagement;
```

---

## 📊 Feature Statistics

### RFM Score Distribution

```sql
SELECT 
    CASE 
        WHEN rfm_score >= 80 THEN '80-100 (Excellent)'
        WHEN rfm_score >= 60 THEN '60-80 (Good)'
        WHEN rfm_score >= 40 THEN '40-60 (Fair)'
        ELSE '0-40 (Poor)'
    END as score_range,
    COUNT(*) as customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM feature_rfm), 2) as percentage
FROM feature_rfm
GROUP BY score_range
ORDER BY score_range DESC;
```

### Churn Risk Distribution

```sql
SELECT 
    churn_risk_category,
    COUNT(*) as customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM feature_churn_risk), 2) as percentage,
    AVG(churn_risk_score) as avg_score
FROM feature_churn_risk
GROUP BY churn_risk_category
ORDER BY 
    CASE churn_risk_category 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        ELSE 4 
    END;
```

---

## 🚀 Next Steps

### Phase 4: ML Model Development

1. **Churn Prediction Model**
   - Training dataset: 80% of customers
   - Validation dataset: 20% of customers
   - Target: 85%+ recall for at-risk customers

2. **Customer Segmentation**
   - 4-5 clusters based on RFM and engagement
   - Targeted retention strategies per segment

3. **Revenue Forecasting**
   - Monthly revenue predictions
   - Product recommendations engine

### Phase 5: Deployment & Monitoring

1. **Prediction API**
   - Real-time churn scoring
   - REST endpoints for predictions

2. **Dashboards**
   - Real-time customer intelligence
   - Segment performance tracking

3. **Monitoring**
   - Model performance tracking
   - Feature drift detection

---

## 📞 Troubleshooting

### Feature Calculation Failed

```powershell
# Check if feature tables exist
$env:PGPASSWORD='sushanth123'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -U postgres -d customer_intelligence -c "\dt feature_*"

# If missing, re-run Phase 3
python phase3_setup.py
```

### Features Empty or NULL

```sql
-- Check which features have NULL values
SELECT * FROM feature_rfm WHERE rfm_score IS NULL LIMIT 10;

-- Recalculate specific feature
DELETE FROM feature_rfm;
-- Then re-run phase3_setup.py
```

---

## 📈 Success Metrics

✅ **Phase 3 Complete When:**
- [ ] All 6 feature tables created
- [ ] ~10,000 rows in each table
- [ ] No NULL values in critical features
- [ ] churn_risk_score ranges 0-100
- [ ] rfm_segment populated correctly
- [ ] engagement_score calculates properly

---

**Status:** ✅ PHASE 3 READY TO EXECUTE  
**Estimated Runtime:** 5-10 minutes  
**Next Phase:** Phase 4 - ML Model Development
