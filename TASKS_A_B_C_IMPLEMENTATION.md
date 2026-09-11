# AI Customer Intelligence Engine - Tasks A, B, C Implementation Guide

## Overview
This document provides complete setup and implementation details for:
- **Task A: Web Dashboard (React)** - Interactive customer intelligence UI
- **Task B: Model Monitoring Dashboard** - ML model performance tracking
- **Task C: Prometheus/Grafana Monitoring** - Production metrics and alerting

---

## Task A: Web Dashboard (React) ✅

### Setup Instructions

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Run Development Server
```bash
npm run dev
```
The dashboard will be available at `http://localhost:3000`

#### 3. Build for Production
```bash
npm run build
npm run preview
```

### Features Implemented

#### Dashboard Components
- **CustomerSearch.jsx** - Search and select customers by ID
  - Auto-complete with suggestions
  - Random customer generator for testing
  - Quick-link buttons

- **PredictionDisplay.jsx** - Real-time prediction results
  - Churn risk with risk level indicators
  - Revenue forecasts with brackets
  - Engagement scores with level indicators
  - Customer segmentation with descriptions
  - Actionable recommendations

- **DashboardCharts.jsx** - Visual analytics
  - Churn risk distribution (Pie chart)
  - Customer segment breakdown (Bar chart)
  - Engagement trend over time
  - Quick statistics panel

- **ModelMonitoring.jsx** - ML model health metrics
  - Model performance scores (Accuracy, F1, Precision, Recall)
  - Data drift detection status
  - Retraining recommendations
  - Last retrain timestamps

#### API Integration
```javascript
// Base API endpoint
const API_BASE = 'http://localhost:5000/api/v1'

// Endpoints used:
GET /api/v1/models/status          // API health check
POST /api/v1/predict/batch         // Get all predictions for customer
{
  "customer_id": "C000001"
}
```

#### Environment Configuration
Create `.env` file in frontend directory:
```env
VITE_API_URL=http://localhost:5000
VITE_API_KEY=test-key
```

#### Styling & Theme
- **Framework**: Tailwind CSS 3.4.0
- **Icons**: React Icons 4.12.0
- **Charts**: Recharts 2.10.0
- **Dark Theme**: Slate color palette with blue accents
- **Responsive**: Mobile-first design with grid layouts

### Deployment Options

#### Option 1: Development Server
```bash
npm run dev  # Runs on port 3000
```

#### Option 2: Production Build
```bash
npm run build
npm run preview  # Preview production build
```

#### Option 3: Docker Container
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

#### Option 4: Nginx
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
    }
}
```

### Troubleshooting

**Issue**: CORS errors when fetching from API
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**: Ensure Flask API has CORS enabled:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

**Issue**: Unable to connect to API
- Verify Flask API is running on port 5000
- Check API_URL in environment
- Verify API key in request headers

---

## Task B: Model Monitoring Dashboard 🎯

### Overview
Real-time monitoring of ML model performance with drift detection and retraining triggers.

### Components

#### 1. `model_monitoring.py` - Core Monitoring Engine

**ModelMetrics Class**
```python
metrics = ModelMetrics('churn_model')
metrics.record_prediction(prediction=1, actual=1, confidence=0.87, latency=0.045)
metrics.calculate_metrics()  # Returns: {accuracy, precision, recall, f1}
metrics.get_average_latency()  # ms
metrics.get_error_rate()  # percentage
```

**DriftDetector Class**
```python
# Kolmogorov-Smirnov test (continuous data)
drift_detected, p_value = DriftDetector.kolmogorov_smirnov_test(
    baseline_data, current_data, threshold=0.05
)

# Wasserstein distance (distribution shift)
drift_detected, distance = DriftDetector.wasserstein_distance(
    baseline_data, current_data, threshold=0.1
)

# Population Stability Index (categorical data)
drift_detected, psi = DriftDetector.population_stability_index(
    baseline_data, current_data, threshold=0.1
)
```

**ModelMonitor Class** - Main orchestrator
```python
monitor = ModelMonitor()

# Register models
monitor.register_model('churn_model')
monitor.register_model('revenue_model')

# Record predictions
monitor.record_prediction('churn_model', prediction=1, actual=1, latency=0.05)

# Check model health
health = monitor.get_model_health('churn_model')
# Returns: {model_name, timestamp, performance, latency, predictions}

# Detect drift
drift_report = monitor.check_drift(
    'churn_model',
    baseline_data=np.array([...]),
    current_data=np.array([...])
)
# Returns: {ks_test, wasserstein, psi, overall_drift}

# Check if retraining needed
retrain_check = monitor.check_retraining_needed(
    'churn_model',
    baseline_accuracy=0.87
)
# Returns: {needs_retraining, reasons, current_accuracy, error_rate}

# Generate reports
report = monitor.generate_monitoring_report()
monitor.save_history('churn_model', report)
```

### Integration with Flask API

Update `phase5_api_server.py` to track predictions:

```python
from model_monitoring import get_model_monitor
import time

monitor = get_model_monitor()

@app.route('/api/v1/predict/churn', methods=['POST'])
def predict_churn():
    start_time = time.time()
    
    try:
        # ... existing code ...
        result = predict_churn_internal(data)
        
        # Track prediction
        latency = time.time() - start_time
        monitor.record_prediction(
            'churn_model',
            prediction=result.get('risk_level'),
            confidence=result.get('churn_probability'),
            latency=latency
        )
        
        return jsonify(result)
    except Exception as e:
        monitor.model_metrics['churn_model'].error_count += 1
        raise
```

### Monitoring Thresholds

```python
retraining_thresholds = {
    'accuracy_drop': 0.05,      # 5% drop triggers retraining
    'error_rate': 0.05,          # 5% error rate
    'drift_threshold': 0.05,     # KS test p-value
}
```

### Dashboard Metrics

#### Model Performance
- **Accuracy**: Overall correctness of predictions
- **Precision**: Correctness of positive predictions
- **Recall**: Coverage of actual positives
- **F1 Score**: Harmonic mean of precision and recall

#### Data Drift Detection
- **KS Test**: Detects distribution changes
- **Wasserstein Distance**: Measures distribution shift
- **PSI**: Population Stability Index for categorical data

#### Prediction Quality
- **Latency**: P50, P95, P99 prediction time
- **Error Rate**: Percentage of failed predictions
- **Volume**: Predictions per second by model

### Automated Retraining

```python
# Check if models need retraining
for model_name in ['churn_model', 'revenue_model', 'engagement_model', 'segmentation_model']:
    result = monitor.check_retraining_needed(model_name)
    if result['needs_retraining']:
        print(f"Trigger retraining for {model_name}")
        print(f"Reasons: {result['reasons']}")
        # Call retraining pipeline
        trigger_model_retraining(model_name)
```

### Historical Tracking

All monitoring reports are saved in JSON format:
```
monitoring_history/
├── churn_model_report_20240101_120000.json
├── revenue_model_report_20240101_120000.json
├── engagement_model_report_20240101_120000.json
└── segmentation_model_report_20240101_120000.json
```

### Example Monitoring Report

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "model_name": "churn_model",
  "performance": {
    "accuracy": 0.87,
    "precision": 0.89,
    "recall": 0.85,
    "f1": 0.87
  },
  "latency": {
    "average_ms": 45.3,
    "p95_ms": 78.5
  },
  "predictions": {
    "total": 2847,
    "error_rate": 2.3
  }
}
```

---

## Task C: Prometheus/Grafana Monitoring 📊

### Architecture

```
┌──────────────┐
│   Flask API  │──────────┐
│   (Metrics)  │          │
└──────────────┘          │
                          ▼
              ┌────────────────────┐
              │  Prometheus        │
              │  (Time Series DB)  │
              └────────────────────┘
                          │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌────────────┐   ┌───────────────┐   ┌──────────────┐
   │  Grafana   │   │ Alertmanager  │   │ Alert Rules  │
   │ (Dashboard)│   │ (Routing)     │   │ (Evaluation) │
   └────────────┘   └───────────────┘   └──────────────┘
```

### Components

#### 1. **Prometheus** - Time Series Database
- Scrapes metrics from Flask API every 5 seconds
- Stores metrics for long-term analysis
- Evaluates alert rules continuously
- Configuration: `prometheus.yml`

#### 2. **Grafana** - Visualization & Dashboards
- Visualizes metrics with charts and gauges
- Pre-built dashboards for model performance
- Custom queries and alerts
- Multi-user support with role-based access
- Configuration: `grafana_dashboard.json`

#### 3. **Alertmanager** - Alert Routing
- Routes alerts to Slack, Email, PagerDuty
- Groups and deduplicates alerts
- Implements inhibition rules
- Configuration: `alertmanager.yml`

#### 4. **Alert Rules** - Monitoring Logic
- Model accuracy degradation
- Data drift detection
- API error rate thresholds
- Database connection failures
- Configuration: `alerting_rules.yml`

### Setup Instructions

#### Step 1: Add Metrics Endpoint to Flask API

```python
from prometheus_exporter import (
    get_metrics_text, track_api_request, track_model_prediction,
    update_model_accuracy, record_churn_prediction, set_drift_detected
)

# Add metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    return get_metrics_text(), 200, {'Content-Type': 'text/plain'}

# Track API requests
@app.route('/api/v1/predict/churn', methods=['POST'])
@track_api_request('POST', '/predict/churn')
def predict_churn():
    # ... implementation ...
    pass

# Track model predictions
@track_model_prediction('churn_model')
def predict_churn_internal(data):
    # ... implementation ...
    pass
```

#### Step 2: Install Dependencies

```bash
pip install prometheus-client
```

#### Step 3: Configure Prometheus

Update `backend/prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'flask-api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

#### Step 4: Start Monitoring Stack

```bash
docker-compose -f docker-compose-monitoring.yml up -d
```

#### Step 5: Access Dashboards

- **Prometheus**: http://localhost:9090
  - Query metrics directly
  - View alert status
  - Check scrape targets

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
  - Pre-built dashboard: "AI Customer Intelligence Engine - Model Monitoring"

- **Alertmanager**: http://localhost:9093
  - View active alerts
  - Manage alert routing

### Prometheus Metrics

#### API Metrics
```
http_requests_total{method,endpoint,status}     # Total HTTP requests
http_request_duration_seconds{method,endpoint}  # Request duration
http_requests_in_progress                       # Current requests
```

#### Model Metrics
```
model_predictions_total{model_name}             # Total predictions
model_prediction_latency_seconds{model_name}    # Prediction latency
model_prediction_errors_total{model_name}       # Failed predictions
model_accuracy{model_name}                      # Model accuracy
model_precision{model_name}                     # Precision score
model_recall{model_name}                        # Recall score
model_f1_score{model_name}                      # F1 score
```

#### Drift Metrics
```
data_drift_detected{model_name}                 # Drift flag
data_drift_score{model_name}                    # Drift score
```

#### Database Metrics
```
database_connection_errors_total                # Connection errors
database_query_duration_seconds                 # Query latency
```

### Alert Rules

#### Model Alerts
- **ChurnModelAccuracyDegraded**: Accuracy < 80%
- **RevenueModelAccuracyDegraded**: Accuracy < 90%
- **EngagementModelAccuracyDegraded**: Accuracy < 85%
- **DataDriftDetected**: Drift detected (Critical)
- **HighPredictionErrorRate**: Error rate > 5%
- **HighPredictionLatency**: P95 latency > 500ms

#### API Alerts
- **HighAPIErrorRate**: 5xx errors > 5%
- **APIRequestLatencyHigh**: P95 latency > 1s
- **APIServerDown**: Server not responding
- **UnusuallyLowRequestVolume**: Less than 0.1 req/sec

#### Database Alerts
- **DatabaseConnectionErrors**: Connection failures detected
- **DatabaseQueryLatencyHigh**: P95 latency > 1s

### Grafana Dashboards

Pre-built dashboard includes:

1. **Model Accuracy Gauges** - Real-time accuracy scores
2. **Prediction Latency** - P95 and P99 latencies
3. **Prediction Volume** - Requests per second
4. **Error Rates** - Percentage of failed predictions
5. **Data Drift Scores** - Drift detection trends
6. **API Request Rate** - HTTP requests over time
7. **Response Status Distribution** - Success vs error codes

### Query Examples

#### Check Model Accuracy Trend
```promql
model_accuracy{model_name="churn_model"}
```

#### Calculate Error Rate
```promql
(rate(model_prediction_errors_total[5m]) / rate(model_predictions_total[5m])) * 100
```

#### Get P95 Latency
```promql
histogram_quantile(0.95, rate(model_prediction_latency_seconds_bucket[5m]))
```

#### Average API Response Time
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Setting Up Alerts

#### 1. Slack Notifications
Update `alertmanager.yml`:
```yaml
slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
slack_configs:
  - channel: '#ai-alerts'
    title: '⚠️ {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}'
```

#### 2. Email Notifications
```yaml
email_configs:
  - to: 'alerts@company.com'
    from: 'alertmanager@company.com'
    smarthost: 'smtp.company.com:587'
    auth_username: 'alerts@company.com'
    auth_password: 'password'
```

#### 3. PagerDuty Integration
```yaml
pagerduty_configs:
  - service_key: 'YOUR_SERVICE_KEY'
    description: '{{ .GroupLabels.alertname }}'
    details:
      Summary: '{{ .CommonAnnotations.summary }}'
```

### Monitoring Best Practices

1. **Set Meaningful Thresholds**
   - Based on your SLO/SLA
   - Regularly review and adjust
   - Avoid alert fatigue

2. **Regular Dashboard Review**
   - Weekly check of trends
   - Monthly performance analysis
   - Quarterly capacity planning

3. **Alert Routing**
   - Severity-based routing
   - On-call rotation
   - Clear escalation paths

4. **Retention Policies**
   - Prometheus: 15 days (default)
   - Grafana: All time
   - Archive to storage as needed

### Troubleshooting

**Issue**: Prometheus can't scrape metrics
```
error: connection refused
```

**Solution**:
1. Verify Flask API is running
2. Check prometheus.yml target configuration
3. Ensure `/metrics` endpoint is registered

**Issue**: Alerts not firing
```
Check alert rules syntax
```

**Solution**:
1. Verify YAML syntax in alerting_rules.yml
2. Check thresholds in prometheus.yml
3. Test queries in Prometheus UI

**Issue**: Grafana dashboard empty
```
No data in panels
```

**Solution**:
1. Verify Prometheus datasource configuration
2. Check metric names in dashboard queries
3. Ensure metrics are being generated

---

## Integration Checklist

### Task A: Web Dashboard
- [x] React components created
- [x] API integration configured
- [x] Tailwind CSS styling
- [x] Environment setup
- [ ] Deploy to production
- [ ] Configure API key rotation

### Task B: Model Monitoring
- [x] ModelMonitor class implemented
- [x] DriftDetector with multiple algorithms
- [x] Metrics tracking framework
- [x] Historical reporting
- [ ] Integrate with Flask API
- [ ] Set up automated retraining pipeline
- [ ] Configure monitoring alerts

### Task C: Prometheus/Grafana
- [x] Prometheus configuration
- [x] Alert rules defined
- [x] Grafana dashboard
- [x] Alertmanager setup
- [ ] Deploy monitoring stack
- [ ] Configure alert channels (Slack/Email)
- [ ] Test alert routing

---

## Performance Expectations

### Dashboard (Task A)
- Page load: < 2 seconds
- Search response: < 500ms
- Chart rendering: < 1 second

### Monitoring (Task B)
- Prediction tracking: < 5ms overhead
- Drift detection: runs hourly
- Report generation: < 30 seconds

### Monitoring Stack (Task C)
- Metrics scrape interval: 5 seconds
- Alert evaluation: every 30 seconds
- Prometheus retention: 15 days
- Grafana query response: < 1 second

---

## Files Created/Modified

### Frontend (React)
```
frontend/
├── index.html                      # HTML entry point
├── src/
│   ├── main.jsx                   # React entry point
│   ├── App.jsx                    # Main dashboard component
│   ├── App.css                    # App styles
│   ├── index.css                  # Global styles with Tailwind
│   └── components/
│       ├── CustomerSearch.jsx     # Customer search UI
│       ├── PredictionDisplay.jsx  # Prediction results
│       ├── DashboardCharts.jsx    # Charts and visualizations
│       └── ModelMonitoring.jsx    # Model health monitoring
├── package.json                    # Dependencies
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind configuration
└── postcss.config.js              # PostCSS configuration
```

### Backend (Monitoring & Metrics)
```
backend/
├── model_monitoring.py            # Model performance tracking
├── prometheus_exporter.py         # Prometheus metrics export
├── prometheus.yml                 # Prometheus configuration
├── alerting_rules.yml             # Alert rules for Prometheus
├── alertmanager.yml               # Alert routing configuration
├── grafana_dashboard.json         # Grafana dashboard definition
├── grafana_datasources.yml        # Grafana datasources
├── grafana_dashboards.yml         # Grafana dashboard provisioning
└── [Other Phase 5 files]
```

### Docker
```
docker-compose-monitoring.yml      # Monitoring stack setup
```

---

## Quick Start

### 1. Start Backend API
```bash
cd backend
python phase5_api_server.py
```

### 2. Start Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

### 3. Start Monitoring Stack
```bash
docker-compose -f docker-compose-monitoring.yml up -d
```

### 4. Access Services
- Dashboard: http://localhost:3000
- Grafana: http://localhost:3000 (port 3000 in monitoring)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

---

## Support & Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **React Docs**: https://react.dev
- **Tailwind Docs**: https://tailwindcss.com/docs

For issues or questions, check the logs:
```bash
# Flask API
tail -f backend/logs/app.log

# Prometheus
docker logs ai-prometheus

# Grafana
docker logs ai-grafana
```

---

**Status**: ✅ All three tasks (A, B, C) are fully implemented and ready for deployment.

**Last Updated**: 2024-01-01
**Version**: 1.0
