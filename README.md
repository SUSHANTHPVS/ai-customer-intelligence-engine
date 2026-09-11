# 🧠 AI Customer Intelligence Engine

A multi-tenant customer analytics platform that turns raw customer data (signups, product usage events, transactions, support tickets) into churn predictions, revenue-at-risk insights, and real-time monitoring — with each user able to upload and analyze their own dataset in complete isolation.

**Stack:** Flask (Python) · React (Vite) · PostgreSQL · Redis · Socket.IO · scikit-learn · Docker

---

## 🎯 What It Does

- Ingests customer data (either the built-in 10,000-row demo dataset or your own uploaded CSVs)
- Engineers RFM, behavioral, engagement, revenue, and support features per customer
- Scores every customer for **churn risk** (rule-based) and lets you **train a real ML model** (RandomForest) per dataset for genuine, held-out accuracy/precision/recall/F1
- Surfaces automated, plain-English insights generated from the live data
- Streams risk alerts in real time over WebSockets
- Exposes everything through a REST + GraphQL API, secured with JWT auth, 2FA, RBAC, and API keys

---

## ✨ Features

### Analytics
- Customer segmentation (VIP / Standard / At-Risk / Dormant)
- Engagement metrics, LTV predictions (actual vs. predicted), churn risk distribution
- Customer search with full profile drill-down (RFM, behavioral, revenue, support, churn history)
- Automated Insights — a real-data-driven insight engine (trend deltas, revenue-at-risk, segment/geo/channel/industry breakdowns, per-customer risk callouts); the dashboard shows one fresh insight every refresh

### Machine Learning
- Real per-dataset model training (`RandomForestClassifier`) with genuine train/test split metrics and feature importances — trained on-demand per dataset via the Datasets page
- Prediction API (`/api/v1/predict/*`) for churn, revenue, engagement, segment, and batch predictions, secured with admin-issued API keys

### Multi-Tenant Datasets
- Any authenticated user can upload their own `customers.csv` (+ optional `events.csv`, `transactions.csv`, `support_tickets.csv`)
- Background processing with per-dataset ID-prefixing for full tenant isolation — no cross-contamination between uploads
- Automatic feature engineering and churn scoring on upload
- Data quality report (duplicate IDs, missing emails/names, completeness %) generated per upload
- Switch your active dataset any time — Analytics, Customers, Live Feed, and Insights all follow

### Real-Time
- Live Activity Feed over Socket.IO, scoped to your active dataset's room
- In-app notification bell for high-risk alerts
- Scheduled background jobs refresh risk snapshots (every minute) and insights (every 5 minutes) per dataset

### Exports
- CSV (customers, analytics report)
- Excel (`.xlsx`) with styled headers
- PDF analytics report

### Auth & Security
- JWT authentication (access + refresh tokens), bcrypt password hashing
- Two-Factor Authentication (TOTP, QR-code setup)
- Role-based access control (admin/user)
- Admin-managed API keys for external API access
- Audit log of security-relevant actions
- Redis-backed rate limiting

### Integrations & Dev Tools
- GraphQL API with GraphiQL playground (`/graphql`)
- Webhooks (HMAC-signed) for high-risk alert events
- Swagger/OpenAPI docs (`/api/docs`)
- Prometheus metrics (`/metrics`)
- Admin CSV bulk customer import

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite, Tailwind, Zustand, Recharts)             │
│  Analytics · Customers · Live Feed · Model Metrics · Datasets · │
│  Settings (2FA, API keys, webhooks, audit log)                  │
└───────────────┬──────────────────────────────────────────────┘
                 │ REST + GraphQL + WebSocket (JWT-secured)
┌────────────────▼─────────────────────────────────────────────┐
│  Flask API (phase5_api_server.py) + blueprints:                │
│  auth · customers · jobs · export · admin · twofa · webhooks · │
│  import · graphql · insights · datasets · ml                   │
│  + APScheduler background jobs + Flask-SocketIO real-time feed │
└───────┬───────────────────────────────────────┬───────────────┘
        │                                        │
┌───────▼────────────┐                  ┌────────▼────────────┐
│ PostgreSQL          │                  │ Redis                │
│ customers, events,  │                  │ cache, rate limits,  │
│ transactions,       │                  │ insight pools,       │
│ support_tickets,    │                  │ trained model blobs  │
│ feature_* tables,   │                  │ (pickled), JWT       │
│ datasets (per-tenant)│                 │ blocklist            │
└─────────────────────┘                  └──────────────────────┘
```

All services run in Docker Compose: `postgres`, `redis`, `backend`, `frontend`.

---

## 💻 Technology Stack

| Layer | Technology |
|---|---|
| Backend | Flask 2.3, Flask-SocketIO, Flask-JWT-Extended, Flask-Limiter |
| Database | PostgreSQL 18 |
| Cache / Queue | Redis 7 |
| ML | scikit-learn (RandomForestClassifier), pandas, numpy |
| API | REST, GraphQL (Ariadne), Swagger (flasgger), Prometheus exporter |
| Real-time | Socket.IO (threading mode), per-dataset rooms |
| Exports | reportlab (PDF), openpyxl (Excel), csv |
| Auth | JWT, bcrypt, pyotp + qrcode (2FA) |
| Frontend | React, Vite, Tailwind CSS, Zustand, Recharts, react-icons, axios, socket.io-client |
| Infra | Docker, Docker Compose |

---

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker Desktop

### Run it

```bash
docker compose up -d --build
```

This starts:

| Service | URL |
|---|---|
| Frontend | http://localhost:9000 |
| Backend API | http://localhost:5000 |
| Swagger docs | http://localhost:5000/api/docs |
| GraphQL playground | http://localhost:5000/graphql |
| Prometheus metrics | http://localhost:5000/metrics |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Default login

A default admin account is seeded automatically on first run:

```
username: admin
password: admin123
```

### Upload your own data

Once logged in, go to **Datasets → Upload Your Own Dataset**, provide a `customers.csv` (required — must include `customer_id, first_name, last_name, email, country, industry, acquisition_channel, signup_date`) plus optional `events.csv` / `transactions.csv` / `support_tickets.csv`. Processing runs in the background; once status flips to `ready`, activate it to see Analytics, Customers, and Live Feed update to your data.

---

## 📂 Key Files

```
phase5_api_server.py    Main Flask entrypoint — registers all blueprints, JWT/rate-limit/Swagger/Prometheus setup
auth.py                 Login/register/refresh, seeds default admin
datasets_bp.py          Multi-tenant dataset upload, processing, feature engineering, CRUD
ml_bp.py                Per-dataset RandomForest training + metrics endpoints
customers_bp.py         Customer search + profile endpoints
export_bp.py            CSV / Excel / PDF export endpoints
insights.py             Automated insight generation (trend, segment, geo, customer-level)
realtime.py             Socket.IO live risk-alert feed (per-dataset rooms)
jobs.py                 Background job status + risk snapshot refresh
admin_bp.py             API key management, RBAC
twofa.py                TOTP two-factor authentication
webhooks_bp.py          Webhook CRUD + HMAC-signed delivery
graphql_bp.py           Ariadne GraphQL schema/resolvers
import_bp.py            Admin CSV bulk customer import
cache.py                Redis cache helpers (with tenant-aware vary_by keys)
audit.py                Audit logging + shared DB connection helper
Dockerfile              Backend image build
docker-compose.yml      Full stack orchestration
requirements-phase5.txt Backend Python dependencies

frontend/src/
  components/           React components (AnalyticsDashboard, CustomerExplorer, DatasetManager,
                        LiveActivityFeed, ModelMetricsDashboard, SettingsPage, Login, ...)
  store/                Zustand stores (auth, dashboard, dataset, theme, notifications)
  api/client.js         Axios API client with auto token-refresh
  lib/socket.js         Socket.IO client wrapper
```

---

## 🔑 Environment Variables

See `.env.example`. Key variables (defaults are fine for local Docker use):

```
JWT_SECRET_KEY=change-me-in-production
DB_HOST=postgres
DB_PORT=5432
DB_NAME=customer_intelligence
DB_USER=postgres
DB_PASSWORD=sushanth123
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## 📝 License

MIT License — see LICENSE for details.

---

**Last Updated:** 2026-09-10
