# 🧠 AI-Powered Business Intelligence & Customer Decision Engine

An end-to-end analytics platform that predicts customer churn, quantifies revenue at risk, and provides actionable intervention recommendations.

**Transform raw customer behavior into executive decisions.**

---

## 🎯 Project Objective

Answer critical business questions:
- **Which customers are likely to leave?** (Churn Prediction)
- **Why are they leaving?** (Explainable AI / SHAP)
- **How much revenue is at risk?** (Revenue-at-Risk Engine)
- **What should we do about it?** (Intervention Recommendations)
- **What-if we could reduce churn?** (Scenario Simulation)

**Scale:** Process 1-10M+ customer events with advanced analytics, ML, and BI.

---

## 🏗️ Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  RAW DATA                                                       │
│  ├─ Customer registrations                                      │
│  ├─ Feature usage events                                        │
│  ├─ Payment transactions                                        │
│  ├─ Support tickets                                             │
│  └─ Marketing interactions                                      │
│         │                                                       │
│         ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ DATA PIPELINE                                          │    │
│  │ ├─ Data Generation (Synthetic)                         │    │
│  │ ├─ Data Cleaning & Validation                          │    │
│  │ ├─ ETL to SQL Warehouse                                │    │
│  │ └─ Feature Engineering                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│         │                                                       │
│         ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ SQL DATA WAREHOUSE (PostgreSQL)                        │    │
│  │ ├─ Fact Tables (events, transactions, support)         │    │
│  │ ├─ Dimension Tables (customer, product, date)          │    │
│  │ ├─ Customer 360° dataset                               │    │
│  │ └─ Pre-aggregated metrics                              │    │
│  └────────────────────────────────────────────────────────┘    │
│         │                                                       │
│    ┌────┴───────┬──────────────┐                               │
│    ▼            ▼              ▼                               │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐                  │
│  │ ANALYTICS│ │ ML MODELS │ │   REPORTS    │                  │
│  │          │ │           │ │              │                  │
│  │ • EDA    │ │ • Churn   │ │ • Cohort     │                  │
│  │ • Cohort │ │   Pred.   │ │ • Retention  │                  │
│  │ • RFM    │ │ • Segm.   │ │ • Attribution│                  │
│  │ • Funnel │ │ • Ranking │ │ • Metrics    │                  │
│  └──────────┘ └───────────┘ └──────────────┘                  │
│         │            │              │                          │
│         └────────────┴──────────────┘                          │
│                  │                                             │
│                  ▼                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ REVENUE-AT-RISK ENGINE                                 │    │
│  │ ├─ Churn Probability × Predicted LTV                   │    │
│  │ ├─ Customer Risk Ranking                               │    │
│  │ └─ Portfolio Risk Assessment                           │    │
│  └────────────────────────────────────────────────────────┘    │
│         │                                                       │
│         ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ INTERVENTION RECOMMENDATION ENGINE                     │    │
│  │ ├─ Rule-based recommendations                          │    │
│  │ ├─ SHAP-based feature importance                       │    │
│  │ ├─ Suggested actions & incentives                      │    │
│  │ └─ Expected ROI per intervention                       │    │
│  └────────────────────────────────────────────────────────┘    │
│         │                                                       │
│    ┌────┴─────────────────────────────┐                       │
│    ▼                                  ▼                       │
│  ┌────────────────────────┐  ┌──────────────────────────┐    │
│  │  INTERACTIVE DASHBOARD │  │  ANALYTICS API (FastAPI)│    │
│  │  (Power BI / Tableau)  │  │                          │    │
│  │                        │  │ Serves:                  │    │
│  │ • Executive Overview   │  │ • Dashboard              │    │
│  │ • Customer Intel       │  │ • Recommendations        │    │
│  │ • Churn Analysis       │  │ • Predictions            │    │
│  │ • Marketing Analytics  │  │ • Explanations           │    │
│  │ • What-if Simulator    │  │ • Scenarios              │    │
│  └────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
│  DEPLOYED: Render (API) + Vercel (Frontend)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
customer-intelligence-engine/
│
├── 📊 data/
│   ├── raw/                      # Raw synthetic data (CSV/Parquet)
│   ├── processed/                # Cleaned, transformed data
│   └── README.md
│
├── 🗄️ sql/
│   ├── schema.sql               # Warehouse schema (fact & dimension tables)
│   ├── transformations.sql      # ETL transformations
│   ├── cohort_analysis.sql      # Cohort & retention queries
│   ├── customer_segmentation.sql# RFM, behavioral segmentation
│   ├── churn_features.sql       # Feature engineering queries
│   └── README.md
│
├── 📓 notebooks/
│   ├── 01_EDA.ipynb             # Exploratory data analysis
│   ├── 02_Cohort_Analysis.ipynb # Cohort retention analysis
│   ├── 03_Segmentation.ipynb    # Customer segmentation
│   ├── 04_Churn_Model.ipynb     # Model training & comparison
│   ├── 05_SHAP_Analysis.ipynb   # Model explainability
│   └── 06_Revenue_Risk.ipynb    # Revenue-at-risk calculations
│
├── 🐍 src/
│   ├── data_generation/         # Synthetic data generation
│   │   ├── __init__.py
│   │   ├── generator.py         # Main data generation logic
│   │   └── config.py            # Data parameters
│   │
│   ├── preprocessing/           # Data cleaning & validation
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   └── validators.py
│   │
│   ├── features/                # Feature engineering
│   │   ├── __init__.py
│   │   ├── customer_360.py      # 360° customer dataset
│   │   ├── behavioral.py        # Behavioral features
│   │   ├── financial.py         # Financial features
│   │   └── temporal.py          # Time-based features
│   │
│   ├── models/                  # ML models
│   │   ├── __init__.py
│   │   ├── churn_model.py       # Churn prediction models
│   │   ├── segmentation.py      # Clustering models
│   │   ├── evaluator.py         # Model evaluation utilities
│   │   └── shap_explainer.py    # SHAP-based explanations
│   │
│   ├── recommendations/         # Intervention engine
│   │   ├── __init__.py
│   │   ├── rules.py             # Rule-based recommendations
│   │   ├── engine.py            # Main recommendation engine
│   │   └── simulator.py         # What-if simulations
│   │
│   └── utils/
│       ├── __init__.py
│       ├── db.py                # Database utilities
│       ├── logger.py            # Logging setup
│       └── config.py            # Global configuration
│
├── 🎨 dashboard/
│   ├── powerbi/                 # Power BI files (.pbix)
│   ├── tableau/                 # Tableau workbooks
│   └── README.md
│
├── 🌐 api/
│   ├── main.py                  # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── predictions.py       # Churn predictions
│   │   ├── recommendations.py   # Intervention recommendations
│   │   ├── customer.py          # Customer 360°
│   │   └── scenarios.py         # What-if simulator
│   │
│   ├── models.py                # Pydantic models
│   ├── config.py                # API configuration
│   └── requirements.txt
│
├── ⚛️ frontend/
│   ├── src/
│   │   ├── pages/               # React pages
│   │   ├── components/          # Reusable components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API calls
│   │   ├── context/             # Context providers
│   │   └── App.jsx
│   │
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── 🧪 tests/
│   ├── test_data_generation.py
│   ├── test_models.py
│   ├── test_api.py
│   └── conftest.py
│
├── 📚 docs/
│   ├── ARCHITECTURE.md          # Detailed architecture
│   ├── DATA_DICTIONARY.md       # Column definitions
│   ├── QUERIES.md               # Important SQL queries
│   ├── ROADMAP.md               # Development roadmap
│   └── DEPLOYMENT.md            # Deployment guide
│
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt             # Python dependencies
├── setup.py
└── LICENSE
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Node.js 18+
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/customer-intelligence-engine.git
cd customer-intelligence-engine

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Create environment file
cp .env.example .env
# Edit .env with your database and API credentials
```

### Phase Workflow

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **Phase 1** | Data Generation & SQL Warehouse | Week 1 | 🔄 In Progress |
| **Phase 2** | Analytics & Cohort Analysis | Week 2 | ⏳ Pending |
| **Phase 3** | Customer Segmentation | Week 2-3 | ⏳ Pending |
| **Phase 4** | Churn Prediction Model | Week 3-4 | ⏳ Pending |
| **Phase 5** | Revenue-at-Risk & Recommendations | Week 4-5 | ⏳ Pending |
| **Phase 6** | Dashboard & BI | Week 5-6 | ⏳ Pending |
| **Phase 7** | FastAPI Backend | Week 6-7 | ⏳ Pending |
| **Phase 8** | React Frontend | Week 7-8 | ⏳ Pending |
| **Phase 9** | Testing & Refinement | Week 8-9 | ⏳ Pending |
| **Phase 10** | Deployment & Documentation | Week 9-10 | ⏳ Pending |

---

## 💻 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Data Generation** | Python, Pandas, Faker |
| **Database** | PostgreSQL (SQL Warehouse) |
| **SQL Analytics** | Advanced SQL (CTEs, Window Functions, Cohorts) |
| **Data Science** | Pandas, NumPy, SciPy |
| **ML/AI** | Scikit-learn, XGBoost, LightGBM |
| **Explainability** | SHAP, Permutation Importance |
| **Statistics** | Statsmodels, Scipy.stats |
| **BI/Dashboard** | Power BI / Tableau |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | React, Vite, Tailwind CSS |
| **Deployment** | Docker, Render, Vercel |
| **Version Control** | Git, GitHub |

---

## 📊 Key Features

### Analytics Layer
- ✅ **EDA:** Comprehensive exploratory data analysis
- ✅ **Cohort Analysis:** Track retention by signup cohort
- ✅ **RFM Segmentation:** Recency, Frequency, Monetary value
- ✅ **Funnel Analysis:** Track user journey
- ✅ **Retention Curves:** Month-over-month retention rates

### ML Layer
- ✅ **Churn Prediction:** XGBoost / LightGBM models
- ✅ **Customer Segmentation:** K-Means + Behavioral clustering
- ✅ **Model Comparison:** Multiple algorithms with performance metrics
- ✅ **Explainability:** SHAP for feature importance & local explanations

### Business Layer
- ✅ **Revenue-at-Risk:** Churn probability × LTV
- ✅ **Customer Risk Scoring:** Ranking by intervention priority
- ✅ **Intervention Recommendations:** Actions & expected ROI
- ✅ **What-if Simulator:** Scenario modeling with sliders

### Frontend Layer
- ✅ **Executive Dashboard:** KPIs, trends, alerts
- ✅ **Customer Intelligence:** Segments, risk profiles
- ✅ **Churn Analytics:** High-risk customers with drivers
- ✅ **Marketing Analytics:** CAC, ROAS, attribution
- ✅ **Scenario Simulator:** Dynamic what-if modeling

---

## 📈 Expected Outcomes (Resume Impact)

Instead of: *"Built a churn prediction model."*

**You'll have:**

> **Customer Intelligence & Revenue Risk Engine** — Engineered an end-to-end analytics platform processing 5M+ behavioral events using advanced SQL, cohort/retention analysis, behavioral segmentation and XGBoost; developed SHAP-based explainability and a revenue-at-risk engine to quantify and prioritize customer retention interventions.

> **Executive BI Dashboard** — Designed and deployed an interactive Power BI dashboard integrating customer 360°, LTV, CAC, cohort retention, churn drivers and what-if simulations, enabling scenario-based estimation of revenue preserved through retention improvements.

> **Recommendation Engine & API** — Built a FastAPI backend serving customer-level intervention recommendations using churn probability, predicted LTV and behavioral risk signals, with real-time analytics capabilities for stakeholder decision support.

---

## 🔗 Resources

- [Architecture Deep Dive](./docs/ARCHITECTURE.md)
- [Data Dictionary](./docs/DATA_DICTIONARY.md)
- [SQL Query Library](./docs/QUERIES.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Development Roadmap](./docs/ROADMAP.md)

---

## 📝 License

MIT License — See LICENSE for details.

---

## 🎓 Learning Resources

- PostgreSQL Window Functions: [PostgreSQL Docs](https://www.postgresql.org/docs/current/functions-window.html)
- XGBoost Tuning: [XGBoost Docs](https://xgboost.readthedocs.io/)
- SHAP Explanations: [SHAP GitHub](https://github.com/slundberg/shap)
- Power BI DAX: [Microsoft Learn](https://learn.microsoft.com/en-us/dax/)
- FastAPI: [FastAPI Docs](https://fastapi.tiangolo.com/)
- React Patterns: [React Docs](https://react.dev/)

---

**Last Updated:** 2026-09-09  
**Project Phase:** Phase 1 - Foundation & Setup  
**Status:** 🟡 In Progress

