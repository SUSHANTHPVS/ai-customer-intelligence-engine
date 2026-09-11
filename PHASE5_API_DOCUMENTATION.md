# PHASE 5: ML Model Prediction API
## Complete API Documentation & Deployment Guide

**Status:** ✅ Ready for Production  
**Version:** 1.0  
**Last Updated:** 2026-09-09  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Authentication](#authentication)
6. [Request/Response Examples](#requestresponse-examples)
7. [Error Handling](#error-handling)
8. [Deployment Guide](#deployment-guide)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Phase 5 API Server exposes all trained ML models from Phase 4 via RESTful HTTP endpoints. It provides real-time predictions for:

- **Churn Risk Prediction** - Identify customers at risk of churning
- **Revenue Forecasting** - Predict customer lifetime revenue
- **Engagement Scoring** - Measure customer engagement (0-100)
- **Segmentation** - Classify customers into 4 segments (STANDARD, DORMANT, AT_RISK, VIP)

### Key Features

✅ **Model Caching** - Models loaded once into memory for fast predictions  
✅ **Database Integration** - Real-time feature retrieval from PostgreSQL  
✅ **Error Handling** - Comprehensive error messages and logging  
✅ **API Versioning** - Endpoint versioning for backward compatibility (/api/v1)  
✅ **CORS Support** - Cross-Origin Resource Sharing enabled  
✅ **Health Monitoring** - Health check endpoint for monitoring  
✅ **Batch Predictions** - Single endpoint for all predictions  
✅ **Scalable Design** - Ready for containerization and load balancing  

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CLIENT APPLICATIONS                       │
│         (Web Apps, Mobile Apps, Batch Processors)          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  FLASK API SERVER (port 5000)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Request Handler Layer                    │  │
│  │  - Validation, CORS, Error Handling                   │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Feature Preparation Layer                   │  │
│  │  - Feature Selection, Encoding, Scaling               │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Prediction Layer (In-Memory)                │  │
│  │  - Churn Model, Revenue Model, Engagement Model,      │  │
│  │    Segmentation Model (all preloaded)                 │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ↓                             ↓
┌──────────────────┐      ┌───────────────────────┐
│   PostgreSQL     │      │    Model Files (PKL)  │
│   Database       │      │    - /models/         │
│   (Features)     │      │    - 8 model files    │
│                  │      │    - scalers & result │
└──────────────────┘      └───────────────────────┘
```

### Component Details

**Flask Application**
- Main WSGI application serving REST endpoints
- Request/response handling with JSON serialization
- Error handling and status code management

**Model Manager**
- Loads all 8 model files into memory on startup
- Caches models for fast repeated predictions
- Provides getter methods for models and scalers

**Feature Preparation**
- Retrieves customer data from PostgreSQL database
- Handles missing values (numeric→median, categorical→'Unknown')
- Applies categorical encoding (LabelEncoder)
- Applies feature scaling (StandardScaler)

**Prediction Models**
- 4 pre-trained RandomForest models (Churn, Revenue, Engagement, Segmentation)
- Pre-fitted scalers for feature normalization
- LabelEncoders for categorical variables

**Database Connection**
- psycopg2 connection pool
- Joins customer features from 6 feature tables
- Connection error handling and retry logic

---

## Installation & Setup

### Prerequisites

- Python 3.14.4
- PostgreSQL 18.6 (running with customer_intelligence database)
- Phase 3 & Phase 4 artifacts (models, scalers, data)

### Step 1: Install Dependencies

```bash
# Install Phase 5 requirements
pip install -r requirements-phase5.txt

# Or individual packages
pip install Flask==2.3.3 Flask-CORS==4.0.0 psycopg2-binary==2.9.9
```

### Step 2: Verify Model Files

Ensure all model files exist in the `models/` directory:

```bash
ls -la models/
# Should show:
# - churn_model.pkl
# - churn_scaler.pkl
# - engagement_model.pkl
# - engagement_scaler.pkl
# - revenue_model.pkl
# - revenue_scaler.pkl
# - segmentation_model.pkl
# - segmentation_scaler.pkl
```

### Step 3: Configure Database Connection

Update `DB_CONFIG` in `phase5_api_server.py`:

```python
DB_CONFIG = {
    'host': 'localhost',        # Change if not local
    'port': 5432,              # Change if non-standard port
    'database': 'customer_intelligence',  # Database name
    'user': 'postgres',        # PostgreSQL user
    'password': 'sushanth123'  # Database password
}
```

### Step 4: Start the API Server

```bash
# Run the server
python phase5_api_server.py

# Expected output:
# ======================================================================
# PHASE 5: ML MODEL PREDICTION API SERVER
# ======================================================================
# [API Server] Loading ML models...
#   ✓ Loaded churn_model
#   ✓ Loaded churn_scaler
#   ... (8 more model/scaler files)
# [API Server] All models loaded successfully
# 
# [API Server] Starting Flask API server...
# [API Server] Available endpoints:
#   POST /api/v1/predict/churn
#   POST /api/v1/predict/revenue
#   POST /api/v1/predict/engagement
#   POST /api/v1/predict/segment
#   POST /api/v1/predict/batch
#   GET  /api/v1/models/status
#   GET  /health
# 
# [API Server] Server running at http://localhost:5000
```

The API is now ready to receive requests!

---

## API Reference

### Base URL
```
http://localhost:5000/api/v1
```

### Standard HTTP Headers

All prediction endpoints require:
```
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

### Response Format

All successful responses return HTTP 200 with JSON:
```json
{
  "customer_id": "C000001",
  "result_field": "value",
  "timestamp": "2026-09-09T19:56:54.123456",
  "model_version": "1.0"
}
```

All errors return JSON with appropriate HTTP status code:
```json
{
  "error": "Error message description"
}
```

---

## Authentication

### Current Implementation
**Type:** Simple API Key  
**Location:** HTTP Header `X-API-Key`

All requests must include the header:
```bash
X-API-Key: your-api-key-here
```

### Example
```bash
curl -X POST http://localhost:5000/api/v1/predict/churn \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000001"}'
```

### Future Enhancement
- Implement OAuth2.0 for production
- Use JWT tokens with expiration
- API key rotation and rate limiting
- Per-user quota management

---

## Request/Response Examples

### 1. Churn Prediction

**Endpoint:** `POST /api/v1/predict/churn`

**Purpose:** Predict churn risk for a customer

**Request:**
```json
{
  "customer_id": "C000005"
}
```

**Response (200 OK):**
```json
{
  "customer_id": "C000005",
  "churn_probability": 0.95,
  "churn_prediction": 1,
  "risk_level": "CRITICAL",
  "timestamp": "2026-09-09T19:56:54.246123",
  "model_version": "1.0"
}
```

**Risk Levels:**
- CRITICAL: churn_probability ≥ 0.80
- HIGH: churn_probability ≥ 0.60
- MEDIUM: churn_probability ≥ 0.40
- LOW: churn_probability < 0.40

**curl Example:**
```bash
curl -X POST http://localhost:5000/api/v1/predict/churn \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000005"}'
```

---

### 2. Revenue Prediction

**Endpoint:** `POST /api/v1/predict/revenue`

**Purpose:** Forecast revenue for a customer

**Request:**
```json
{
  "customer_id": "C000002"
}
```

**Response (200 OK):**
```json
{
  "customer_id": "C000002",
  "revenue_forecast": 1250.75,
  "revenue_bracket": "HIGH",
  "timestamp": "2026-09-09T19:56:54.246123",
  "model_version": "1.0"
}
```

**Revenue Brackets:**
- VERY HIGH: revenue_forecast ≥ $1500
- HIGH: revenue_forecast ≥ $1000
- MEDIUM: revenue_forecast ≥ $500
- LOW: revenue_forecast ≥ $200
- MINIMAL: revenue_forecast < $200

**curl Example:**
```bash
curl -X POST http://localhost:5000/api/v1/predict/revenue \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000002"}'
```

---

### 3. Engagement Prediction

**Endpoint:** `POST /api/v1/predict/engagement`

**Purpose:** Predict customer engagement score (0-100)

**Request:**
```json
{
  "customer_id": "C000010"
}
```

**Response (200 OK):**
```json
{
  "customer_id": "C000010",
  "engagement_score": 85.5,
  "engagement_level": "HIGH",
  "timestamp": "2026-09-09T19:56:54.246123",
  "model_version": "1.0"
}
```

**Engagement Levels:**
- VERY HIGH: engagement_score ≥ 80
- HIGH: engagement_score ≥ 60
- MEDIUM: engagement_score ≥ 40
- LOW: engagement_score ≥ 20
- VERY LOW: engagement_score < 20

**curl Example:**
```bash
curl -X POST http://localhost:5000/api/v1/predict/engagement \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000010"}'
```

---

### 4. Segmentation/Clustering

**Endpoint:** `POST /api/v1/predict/segment`

**Purpose:** Classify customer into segment (cluster)

**Request:**
```json
{
  "customer_id": "C000020"
}
```

**Response (200 OK):**
```json
{
  "customer_id": "C000020",
  "cluster": 3,
  "segment_name": "VIP",
  "description": "High-value, highly engaged customer",
  "timestamp": "2026-09-09T19:56:54.246123",
  "model_version": "1.0"
}
```

**Segment Types:**
| Cluster | Segment | Description |
|---------|---------|-------------|
| 0 | STANDARD | Regular customers with normal engagement |
| 1 | DORMANT | Inactive customers, at risk of churn |
| 2 | AT_RISK | Disengaged customers requiring attention |
| 3 | VIP | High-value, highly engaged customers |

**curl Example:**
```bash
curl -X POST http://localhost:5000/api/v1/predict/segment \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000020"}'
```

---

### 5. Batch Predictions (All-in-One)

**Endpoint:** `POST /api/v1/predict/batch`

**Purpose:** Get all predictions for a customer in one request

**Request:**
```json
{
  "customer_id": "C000001"
}
```

**Response (200 OK):**
```json
{
  "customer_id": "C000001",
  "churn": {
    "churn_probability": 0.0,
    "churn_prediction": 0,
    "risk_level": "LOW"
  },
  "revenue": {
    "revenue_forecast": 999.0,
    "revenue_bracket": "HIGH"
  },
  "engagement": {
    "engagement_score": 100.0,
    "engagement_level": "VERY HIGH"
  },
  "segment": {
    "cluster": 3,
    "segment_name": "VIP",
    "description": "High-value, highly engaged customer"
  },
  "timestamp": "2026-09-09T19:56:54.246123"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:5000/api/v1/predict/batch \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C000001"}'
```

---

### 6. Model Status

**Endpoint:** `GET /api/v1/models/status`

**Purpose:** Check which models are loaded

**Response (200 OK):**
```json
{
  "models_loaded": true,
  "models": [
    "churn_model",
    "engagement_model",
    "revenue_model",
    "segmentation_model"
  ],
  "scalers": [
    "churn_scaler",
    "engagement_scaler",
    "revenue_scaler",
    "segmentation_scaler"
  ],
  "timestamp": "2026-09-09T19:56:54.246123"
}
```

**curl Example:**
```bash
curl -X GET http://localhost:5000/api/v1/models/status \
  -H "X-API-Key: test-key"
```

---

### 7. Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify API server is running (no auth required)

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-09-09T19:56:54.246123",
  "models_loaded": true
}
```

**curl Example:**
```bash
curl -X GET http://localhost:5000/health
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Returned |
|------|---------|---------------|
| 200 | OK | Successful prediction |
| 400 | Bad Request | Missing/invalid JSON or parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Customer not found in database, or invalid endpoint |
| 500 | Internal Error | Unexpected server error |

### Error Response Format

```json
{
  "error": "Descriptive error message"
}
```

### Common Errors

**1. Missing API Key**
```
HTTP 401
{
  "error": "Missing API key"
}
```

**2. Missing customer_id**
```
HTTP 400
{
  "error": "Invalid input: Missing customer_id"
}
```

**3. Customer Not Found**
```
HTTP 404
{
  "error": "Customer not found: C999999"
}
```

**4. No JSON Data**
```
HTTP 400
{
  "error": "No JSON data provided"
}
```

**5. Invalid Endpoint**
```
HTTP 404
{
  "error": "Endpoint not found"
}
```

### Logging

All errors are logged to `api_server.log`:
```
2026-09-09 19:56:54,246 - phase5_api_server - ERROR - Validation error: Missing customer_id
2026-09-09 19:56:54,247 - phase5_api_server - ERROR - Unexpected error: Database connection failed
```

---

## Deployment Guide

### Local Development (Current Setup)

```bash
# 1. Start API server
python phase5_api_server.py

# 2. In another terminal, test endpoints
curl -X GET http://localhost:5000/health
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.14

WORKDIR /app

COPY requirements-phase5.txt .
RUN pip install -r requirements-phase5.txt

COPY phase5_api_server.py .
COPY models/ models/

EXPOSE 5000

CMD ["python", "phase5_api_server.py"]
```

**Build & Run:**
```bash
# Build image
docker build -t ai-customer-intelligence:phase5 .

# Run container
docker run -p 5000:5000 \
  -e DB_HOST=postgres-host \
  -e DB_PASSWORD=your-password \
  ai-customer-intelligence:phase5
```

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-api-server
  template:
    metadata:
      labels:
        app: ml-api-server
    spec:
      containers:
      - name: api
        image: ai-customer-intelligence:phase5
        ports:
        - containerPort: 5000
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: db_host
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ml-api-service
spec:
  selector:
    app: ml-api-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Production Considerations

1. **Use Gunicorn/uWSGI** instead of Flask dev server
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 phase5_api_server:app
   ```

2. **Enable HTTPS/SSL** - Use nginx reverse proxy or cloud load balancer

3. **Rate Limiting** - Add rate limiter to prevent abuse
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.headers.get('X-API-Key'))
   ```

4. **Monitoring** - Integrate with Prometheus/Grafana for metrics

5. **Caching** - Use Redis for feature caching
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   ```

6. **Database Connection Pool** - Use pgBouncer for connection pooling

---

## Monitoring & Logging

### Log Files

**api_server.log** - Contains all server activity:
```
2026-09-09 19:56:54,246 - phase5_api_server - INFO - [API Server] Loading ML models...
2026-09-09 19:56:54,250 - phase5_api_server - INFO -   ✓ Loaded churn_model
2026-09-09 19:56:54,256 - phase5_api_server - INFO -   ✓ Loaded churn_scaler
...
2026-09-09 19:56:55,500 - phase5_api_server - INFO - [API Server] Server running at http://localhost:5000
```

### Health Check Monitoring

Monitor the `/health` endpoint regularly:
```bash
# Check every 10 seconds
while true; do
  curl -s http://localhost:5000/health | jq .
  sleep 10
done
```

### Performance Metrics to Track

1. **Prediction Latency** - Time to generate a prediction
   - Target: < 100ms per prediction
   - Track via `/api/v1/predict/*` response times

2. **Model Load Time** - Time to load all models
   - Displayed at server startup
   - Target: < 30 seconds

3. **Database Query Time** - Time to fetch customer features
   - Should be < 50ms for normal customers
   - Check for slow queries

4. **API Throughput** - Requests per second
   - Monitor active connections
   - Target: 100+ RPS with 3 replicas

5. **Error Rate** - Percentage of failed predictions
   - Target: < 0.1% error rate
   - Investigate customer not found errors

### Useful Commands

```bash
# View real-time logs
tail -f api_server.log

# Count errors in logs
grep "ERROR" api_server.log | wc -l

# Monitor API performance
watch -n 1 'tail -20 api_server.log'

# Test endpoint response time
time curl -X GET http://localhost:5000/health
```

---

## Troubleshooting

### Issue: Models Failed to Load

**Symptom:**
```
[API Server] ✗ Model file not found: models/churn_model.pkl
```

**Solution:**
1. Verify Phase 4 completed successfully: `ls -la models/`
2. Ensure all 8 pickle files exist in `models/` directory
3. Check file permissions: `chmod 644 models/*.pkl`
4. Verify current working directory: `pwd` should be project root

### Issue: Database Connection Failed

**Symptom:**
```
Database connection failed: FATAL: password authentication failed
```

**Solution:**
1. Verify PostgreSQL is running: `psql -U postgres -d customer_intelligence`
2. Check connection credentials in `DB_CONFIG`
3. Verify database and tables exist:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema='public';
   ```
4. Check firewall/network connectivity to database host

### Issue: Customer Not Found

**Symptom:**
```
HTTP 404
{"error": "Customer not found: C000001"}
```

**Solution:**
1. Verify customer exists in database:
   ```sql
   SELECT COUNT(*) FROM customers WHERE customer_id='C000001';
   ```
2. Verify feature tables are populated:
   ```sql
   SELECT COUNT(*) FROM feature_rfm;
   SELECT COUNT(*) FROM feature_behavioral;
   ```
3. Check LEFT JOIN results in `query_customer_data()` function

### Issue: API Server Won't Start

**Symptom:**
```
Address already in use: ('0.0.0.0', 5000)
```

**Solution:**
1. Find process using port 5000: `lsof -i :5000`
2. Kill existing process: `kill -9 PID`
3. Or use different port: Modify line `app.run(port=5001, ...)`

### Issue: Prediction Takes Too Long

**Symptom:**
```
Request takes > 1 second to complete
```

**Possible Causes & Solutions:**
1. **Slow database query** - Add indexes to customer tables
   ```sql
   CREATE INDEX idx_customer_id ON customers(customer_id);
   ```
2. **Network latency** - Ensure database and API server are on same network
3. **Model size** - Verify models are loaded in memory (check startup log)
4. **High CPU usage** - Increase server resources or add replicas

### Issue: Out of Memory Error

**Symptom:**
```
MemoryError: Unable to allocate 2.50 GiB for an array
```

**Solution:**
1. Models use ~500MB-1GB of RAM
2. Ensure server has at least 2GB available memory
3. Check for memory leaks in logs
4. Reduce `max_workers` if using parallel processing

### Issue: Categorical Encoding Error

**Symptom:**
```
ValueError: y contains previously unseen labels: 'India'
```

**Solution:**
1. This happens if LabelEncoder encounters new category
2. Check that encoder was trained on all categories
3. Verify data consistency between Phase 4 and API server
4. Re-run Phase 4 if customer countries have changed

---

## Performance Optimization Tips

### 1. Cache Predictions

For frequently requested customers, cache recent predictions:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_customer_predictions(customer_id):
    return predict_batch_internal(customer_id)
```

### 2. Batch API Calls

Instead of individual requests:
```bash
# Inefficient: 1000 separate requests
for i in {1..1000}; do
  curl -X POST http://localhost:5000/api/v1/predict/churn \
    -H "X-API-Key: key" \
    -d "{\"customer_id\": \"C$i\"}"
done

# Better: Single batch request (once implemented)
curl -X POST http://localhost:5000/api/v1/predict/batch \
  -H "X-API-Key: key" \
  -d '{"customer_ids": ["C1", "C2", ..., "C1000"]}'
```

### 3. Use Connection Pooling

```python
from psycopg2 import pool

db_pool = pool.SimpleConnectionPool(5, 20, **DB_CONFIG)

def get_db_connection():
    return db_pool.getconn()

def return_db_connection(conn):
    db_pool.putconn(conn)
```

### 4. Implement Async Predictions

```python
from celery import Celery

celery = Celery('api', broker='redis://localhost:6379')

@celery.task
def predict_async(customer_id):
    return predict_churn_internal(customer_id)

# Call with: result = predict_async.delay('C000001')
# Check result: result.get()
```

---

## Next Steps

1. ✅ **Phase 5 API Complete** - All endpoints deployed
2. ⏳ **Phase 6: Web Dashboard** - Create UI for predictions
3. ⏳ **Phase 7: Mobile App** - Mobile access to predictions
4. ⏳ **Phase 8: Analytics & Reporting** - Business intelligence layer
5. ⏳ **Phase 9: Advanced ML** - Ensemble models, feature engineering improvements
6. ⏳ **Phase 10: Production Hardening** - Security, scalability, compliance

---

## Support & Contact

For issues or questions:
1. Check `api_server.log` for detailed error messages
2. Review troubleshooting section above
3. Verify database connectivity
4. Ensure all Phase 4 artifacts are present

---

**API Documentation Complete ✅**  
**Status: Production Ready**  
**Last Updated:** 2026-09-09  
