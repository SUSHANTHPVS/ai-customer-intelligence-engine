# Architecture Deep Dive

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER INTELLIGENCE ENGINE                 │
└─────────────────────────────────────────────────────────────────┘

1. DATA LAYER
   ├─ Synthetic Data Generation (Python)
   ├─ CSV/Parquet Files
   └─ PostgreSQL Data Warehouse

2. ANALYTICS LAYER
   ├─ SQL Analytics & Transformations
   ├─ Cohort Analysis
   ├─ RFM Segmentation
   ├─ Feature Engineering
   └─ Materialized Views

3. ML LAYER
   ├─ Churn Prediction (XGBoost/LightGBM)
   ├─ Customer Segmentation (K-Means)
   ├─ Model Evaluation
   └─ SHAP Explainability

4. BUSINESS LOGIC LAYER
   ├─ Revenue-at-Risk Calculation
   ├─ Customer Risk Scoring
   ├─ Intervention Recommendations
   └─ What-if Simulation

5. API LAYER
   ├─ FastAPI Backend
   ├─ REST Endpoints
   ├─ Authentication (JWT)
   └─ Rate Limiting

6. PRESENTATION LAYER
   ├─ React Dashboard
   ├─ Interactive Visualizations
   ├─ What-if Simulator UI
   └─ Mobile Responsive

7. BI LAYER
   ├─ Power BI Reports
   ├─ Executive Dashboard
   ├─ Self-Service Analytics
   └─ Scheduled Refreshes
```

## Data Flow

```
RAW EVENTS
    ↓
SYNTHETIC DATA GENERATOR
    ↓
CSV/PARQUET FILES (data/raw/)
    ↓
POSTGRES LOADER (ETL)
    ↓
DATA WAREHOUSE (Star Schema)
    ├─ Fact Tables
    ├─ Dimension Tables
    └─ Materialized Views
    ↓
SQL TRANSFORMATIONS
    ├─ Feature Engineering
    ├─ Customer 360°
    └─ Aggregations
    ↓
ANALYTICS + ML
    ├─ Cohort Analysis
    ├─ Churn Model Training
    ├─ Segmentation
    └─ SHAP Explanations
    ↓
BUSINESS LOGIC
    ├─ Revenue-at-Risk
    ├─ Risk Scoring
    └─ Recommendations
    ↓
API LAYER (FastAPI)
    ├─ Predictions Endpoint
    ├─ Recommendations Endpoint
    ├─ Customer 360° Endpoint
    └─ Scenario Endpoint
    ↓
FRONTEND & BI
    ├─ React Dashboard
    ├─ Power BI Dashboard
    └─ What-if Simulator
    ↓
STAKEHOLDERS
    ├─ Executives
    ├─ Customer Success Teams
    └─ Product Teams
```

## Component Details

### 1. Data Generation (`src/data_generation/`)

**Purpose**: Generate realistic synthetic customer data

**Components**:
- `SyntheticDataGenerator`: Main generator class
- Customer profile generation
- Event stream simulation
- Transaction history creation
- Support ticket generation

**Output**:
- `data/raw/customers.csv` - 10K customers
- `data/raw/events.csv` - 1M events
- `data/raw/transactions.csv` - ~20K transactions
- `data/raw/support_tickets.csv` - ~5K tickets

**Rationale**: 
- Demonstrates ability to work with realistic, large-scale data
- No privacy concerns with synthetic data
- Reproducible with fixed seed

### 2. Data Warehouse (`sql/`)

**Schema**: Star Schema

```
                dim_product
                     |
                     |
dim_date ------- fact_events ------- dim_customer
                     |                    |
                     |              dim_campaign
            fact_transactions
                     |
            fact_support
                     |
            fact_marketing
```

**Tables**:

**Dimension Tables** (Descriptive):
- `dim_date`: Calendar with holidays, weeks, quarters
- `dim_customer`: Demographics, acquisition, segmentation
- `dim_product`: Product catalog
- `dim_campaign`: Marketing campaigns

**Fact Tables** (Measurements):
- `fact_events`: User interactions (login, feature_usage, etc.)
- `fact_transactions`: Revenue events (subscription, upgrade, refund)
- `fact_support`: Support tickets (resolution time, satisfaction)
- `fact_marketing`: Campaign metrics (impressions, clicks, conversions)

**Materialized Views**:
- `v_customer_metrics`: Precomputed customer KPIs (updated daily)

**Benefits**:
- Normalized structure prevents data duplication
- Efficient aggregation queries
- Materialized views for performance
- Easily extensible for new metrics

### 3. Analytics Layer (`sql/analytics.sql`)

**Key Queries**:

1. **Cohort Analysis**
   - Track customer cohorts by signup month
   - Calculate retention rates over time
   - Identify which cohorts are most valuable

2. **Churn Analysis**
   - Define churn: no activity for 30+ days
   - Segment into CHURNED, AT_RISK, ACTIVE
   - Analyze churn patterns

3. **RFM Segmentation**
   - Recency: Days since last activity
   - Frequency: Total interactions in 90 days
   - Monetary: Total revenue
   - Scores 1-5 for each, then segment

4. **Funnel Analysis**
   - Track user progression through event types
   - Calculate conversion rates between stages
   - Identify drop-off points

5. **Revenue Analysis**
   - Monthly revenue trends
   - Customer lifetime value projection
   - Revenue per segment

### 4. Feature Engineering (`src/features/`)

**Customer 360° Dataset** includes:

**Behavioral Features**:
- Total events in last 30/90 days
- Session count & duration
- Feature adoption
- Engagement score

**Financial Features**:
- Total revenue (lifetime)
- Revenue trend (last 30/90 days)
- Average order value
- Payment success rate

**Temporal Features**:
- Days since signup
- Days since last event
- Account tenure
- Seasonality

**Categorical Features**:
- Acquisition channel
- Customer segment (RFM)
- Plan tier
- Industry/Country

### 5. Machine Learning Models (`src/models/`)

**Churn Prediction Pipeline**:

```
Customer 360° Dataset
         ↓
  Feature Scaling
         ↓
  Train/Test Split (80/20)
         ↓
  Model Training
  ├─ Logistic Regression (baseline)
  ├─ Random Forest
  ├─ XGBoost
  └─ LightGBM
         ↓
  Model Evaluation
  ├─ Accuracy
  ├─ Precision
  ├─ Recall
  ├─ ROC-AUC
  └─ Feature Importance
         ↓
  Best Model Selection (XGBoost)
         ↓
  SHAP Explainability
         ↓
  Production Model (Pickled)
```

**Model Selection Rationale**:
- **Logistic Regression**: Fast baseline, interpretable
- **Random Forest**: Non-linear, handles interactions
- **XGBoost**: SOTA performance, feature importance
- **LightGBM**: Fast training, memory efficient

**Churn Definition**:
- Binary: Churned = no activity for 30+ days
- Predicted for next 30 days

**Key Metric**:
- ROC-AUC: Balances sensitivity/specificity
- Recall: Catch at-risk customers

### 6. Business Logic Layer (`src/recommendations/`)

**Revenue-at-Risk Engine**:

```
Customer Churn Probability (from model)
         ×
Customer Lifetime Value (from historical data)
         =
Revenue at Risk ($)
```

Example:
```
Customer A:
- Churn Probability: 82%
- Predicted LTV (36 months): ₹3,00,000
- Revenue at Risk = 0.82 × ₹3,00,000 = ₹2,46,000
```

**Customer Risk Scoring**:
```
Risk Score = 
    (Churn Prob × 0.5) +      # Churn likelihood
    (Revenue at Risk / Max × 0.3) +  # Financial impact
    (Days Inactive / 90 × 0.2)  # Activity recency
```

**Recommendation Engine**:

```
For each high-risk customer:
  1. Identify primary churn drivers (SHAP)
  2. Match to pre-defined rule sets
  3. Recommend action:
     - Customer Success manager assignment
     - Discount or feature upgrade offer
     - Priority support
     - Special incentive
  4. Estimate intervention ROI
```

**What-if Simulator**:
```
Current State:
- Churn Rate: 14.8%
- Customers Churned (annual): 3,500
- Revenue Lost: ₹5.2 Cr

Scenario:
- Churn Reduction: 5% → 9.8%
- Customers Retained: +1,750
- Revenue Preserved: ₹2.6 Cr
- Campaign Cost: ₹50 Lakh
- ROI: 420%
```

### 7. API Layer (`api/`)

**Endpoints**:

```
GET  /api/health
POST /api/predictions/churn
GET  /api/predictions/churn/{customer_id}
GET  /api/customer/{customer_id}
GET  /api/recommendations/{customer_id}
POST /api/scenarios/simulate
```

**Request/Response Examples**:

```python
# Churn Prediction
GET /api/predictions/churn/C000001

Response:
{
  "customer_id": "C000001",
  "churn_probability": 0.82,
  "risk_level": "HIGH",
  "primary_drivers": [
    {"feature": "feature_usage", "importance": 0.35},
    {"feature": "support_complaints", "importance": 0.28},
  ]
}

# Customer 360°
GET /api/customer/C000001

Response:
{
  "profile": {...},
  "metrics": {
    "total_revenue": 5000,
    "events_last_30d": 45,
    "avg_session_duration": 340,
  },
  "risk": {...}
}

# Recommendations
GET /api/recommendations/C000001

Response:
{
  "customer_id": "C000001",
  "risk_score": 8.2,
  "recommendations": [
    {
      "action": "assign_csm",
      "reason": "High-value customer with declining engagement",
      "estimated_roi": 0.65
    }
  ]
}
```

### 8. Frontend (`frontend/`)

**Pages**:

1. **Dashboard**: Executive overview
2. **Customer Intelligence**: Segment analysis
3. **Churn Analytics**: High-risk customers
4. **Marketing Analytics**: Campaign performance
5. **Simulator**: What-if scenarios

**Key Components**:
- Metric Cards (KPIs)
- Charts (Recharts)
- Tables (Customers, Recommendations)
- Sliders (Scenario simulator)
- Filters (Country, Industry, Segment)

### 9. BI Layer (`dashboard/`)

**Power BI Report Pages**:

1. **Executive Overview**: High-level KPIs
2. **Customer Intel**: Segments & profiles
3. **Churn Drivers**: SHAP analysis
4. **What-if**: Scenario modeling
5. **Marketing**: CAC, ROAS, attribution

## Technology Stack Rationale

| Component | Technology | Why |
|-----------|-----------|-----|
| **Data Gen** | Python + Faker | Fast, realistic, reproducible |
| **Database** | PostgreSQL | Powerful SQL, free, scalable |
| **ML** | XGBoost + Scikit-learn | SOTA, proven in production |
| **Explainability** | SHAP | Industry standard |
| **API** | FastAPI | Modern, fast, auto-docs |
| **Frontend** | React + Vite | Component-based, fast builds |
| **BI** | Power BI | Professional, enterprise |
| **Deployment** | Docker + Render/Vercel | Containerized, cloud-native |

## Performance Considerations

1. **Database**:
   - Partition fact tables by date
   - Index on foreign keys & common filters
   - Materialized views for frequent queries
   - Connection pooling (pgbouncer)

2. **ML**:
   - Batch predictions for efficiency
   - Model caching/versioning
   - Async endpoints for long-running tasks
   - Model monitoring for drift detection

3. **API**:
   - Caching (Redis) for frequent queries
   - Rate limiting to prevent abuse
   - Async endpoints for I/O operations
   - Database connection pooling

4. **Frontend**:
   - Code splitting & lazy loading
   - Image optimization
   - Component memoization
   - Virtual scrolling for large tables

## Scalability Path

**Current (MVP)**:
- Single PostgreSQL instance
- Batch predictions daily
- Single API server

**Growth (Scale 1)**:
- Read replicas for analytics
- Real-time predictions via message queue
- Multiple API servers with load balancing
- Redis caching layer

**Enterprise (Scale 2)**:
- Sharded database across regions
- Real-time feature store
- Kubernetes orchestration
- Data lake for historical analysis
- Real-time recommendation engine

## Security Considerations

1. **Authentication**: JWT tokens
2. **Authorization**: Role-based access (admin/analyst/viewer)
3. **Data Protection**: Encryption at rest & in transit
4. **Input Validation**: Pydantic models for API
5. **SQL Injection**: Parameterized queries via SQLAlchemy
6. **Secrets Management**: Environment variables, no hardcoding

## Monitoring & Observability

1. **Logging**: Structured logs to file
2. **Metrics**: API response times, prediction latency
3. **Alerts**: Churn rate anomalies, model drift
4. **Dashboards**: Grafana for system health
5. **Tracing**: Request tracing for debugging

---

**Last Updated**: 2026-09-09  
**Version**: 0.1.0
