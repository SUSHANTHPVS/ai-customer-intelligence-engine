# Troubleshooting Guide - Tasks A, B, C

## Quick Diagnostic

Run this validation script to check your setup:
```bash
python validate_setup.py
```

This will verify:
- ✅ All required files exist
- ✅ Python packages installed
- ✅ Backend API running
- ✅ Prometheus running
- ✅ Grafana running
- ✅ Metrics endpoint responding

---

## Task A: Web Dashboard Issues

### Issue 1: "Cannot connect to API" or "API not responding"
**Error**: `Failed to fetch data from API`

**Diagnosis**:
```bash
# Check if Flask API is running
curl http://localhost:5000/api/v1/models/status

# Should return JSON with models list
```

**Solutions**:
1. **Start the Flask API**:
   ```bash
   cd backend
   python phase5_api_server.py
   ```

2. **Verify port 5000 is available**:
   ```bash
   # On Windows
   netstat -ano | findstr :5000
   
   # On Mac/Linux
   lsof -i :5000
   ```

3. **Check CORS is enabled in Flask**:
   ```python
   # In phase5_api_server.py
   from flask_cors import CORS
   CORS(app)
   ```

4. **Verify API endpoint in frontend**:
   - Check `vite.config.js` proxy configuration
   - Check `.env` file has correct API URL
   - Default: `http://localhost:5000`

### Issue 2: "Dashboard shows 'Loading...' forever"
**Error**: Spinner spinning indefinitely

**Diagnosis**:
```javascript
// Open browser console (F12)
// Look for network errors
// Check network tab for failed requests
```

**Solutions**:
1. **Check API is responding**:
   ```bash
   curl -X POST http://localhost:5000/api/v1/predict/batch \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"customer_id": "C000001"}'
   ```

2. **Check customer ID exists**:
   - Valid IDs: C000001 to C010000
   - Try a different ID if current one fails

3. **Check browser console for errors**:
   - Press F12 to open DevTools
   - Go to Console tab
   - Look for red error messages

### Issue 3: "No predictions displayed" or "Empty results"
**Error**: Customer search returns empty

**Solutions**:
1. **Verify database has data**:
   ```python
   # Run in backend directory
   import pandas as pd
   from sqlalchemy import create_engine
   
   engine = create_engine('postgresql://postgres:sushanth123@localhost:5432/customer_intelligence')
   df = pd.read_sql('SELECT COUNT(*) as count FROM customers', engine)
   print(df)  # Should show count > 0
   ```

2. **Check API response**:
   ```bash
   curl -X POST http://localhost:5000/api/v1/predict/batch \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"customer_id": "C000001"}' | jq .
   ```

3. **Verify models are loaded**:
   ```bash
   curl http://localhost:5000/api/v1/models/status | jq .
   # Should show all 4 models as "loaded": true
   ```

### Issue 4: "Charts not rendering" or "Empty visualizations"
**Error**: Chart areas show but no data

**Solutions**:
1. **Check prediction data**:
   - Make sure API returns predictions
   - Verify prediction values are in valid ranges

2. **Clear browser cache**:
   - Press Ctrl+Shift+Delete
   - Clear all data
   - Reload page

3. **Check Recharts installation**:
   ```bash
   cd frontend
   npm list recharts
   ```

---

## Task B: Model Monitoring Issues

### Issue 1: "Model monitoring module not found"
**Error**: `ModuleNotFoundError: No module named 'model_monitoring'`

**Solutions**:
1. **Verify file exists**:
   ```bash
   ls backend/model_monitoring.py
   ```

2. **Check Python path**:
   ```bash
   # From backend directory
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python phase5_api_server.py
   ```

3. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Issue 2: "Drift detection not triggering"
**Error**: Drift never detected even when it should be

**Solutions**:
1. **Check baseline data**:
   ```python
   from model_monitoring import get_model_monitor
   monitor = get_model_monitor()
   
   # Verify baseline is set
   metrics = monitor.model_metrics['churn_model']
   print(f"Baseline samples: {len(metrics.baseline_data)}")
   ```

2. **Lower drift threshold for testing**:
   ```python
   # In model_monitoring.py
   drift_thresholds = {
       'ks_test': 0.10,  # Change from 0.05 to 0.10
       'wasserstein': 0.2,  # Change from 0.1 to 0.2
       'psi': 0.2  # Change from 0.1 to 0.2
   }
   ```

3. **Manually test drift detection**:
   ```python
   from model_monitoring import DriftDetector
   import numpy as np
   
   baseline = np.random.normal(0, 1, 100)
   current = np.random.normal(1, 1, 100)  # Shifted distribution
   
   result, p_value = DriftDetector.kolmogorov_smirnov_test(
       baseline, current, threshold=0.05
   )
   print(f"Drift detected: {result}, p-value: {p_value}")
   ```

### Issue 3: "Model metrics showing as 0 or None"
**Error**: Accuracy always 0%, latency None

**Solutions**:
1. **Ensure predictions are recorded**:
   ```python
   # Add this to Flask API
   monitor.record_prediction(
       'churn_model',
       prediction=1,
       actual=1,
       confidence=0.87,
       latency=0.045
   )
   ```

2. **Check circular buffer size**:
   ```python
   # In model_monitoring.py
   metrics = monitor.model_metrics['churn_model']
   print(f"Buffer size: {len(metrics.predictions)}")
   print(f"Predictions: {metrics.predictions}")
   ```

3. **Verify actual values are provided**:
   - Don't pass `actual=None`
   - All predictions need actual labels for accuracy calculation

### Issue 4: "Historical reports not saving"
**Error**: monitoring_history/ folder empty

**Solutions**:
1. **Create directory if missing**:
   ```bash
   mkdir -p backend/monitoring_history
   chmod 755 backend/monitoring_history
   ```

2. **Check write permissions**:
   ```bash
   # Test write
   touch backend/monitoring_history/test.json
   rm backend/monitoring_history/test.json
   ```

3. **Verify save_history is called**:
   ```python
   report = monitor.generate_monitoring_report()
   monitor.save_history('churn_model', report)
   ```

---

## Task C: Prometheus/Grafana Issues

### Issue 1: "Prometheus won't start in Docker"
**Error**: `docker-compose up` fails or container keeps restarting

**Solutions**:
1. **Check port conflicts**:
   ```bash
   # Port 9090 might be in use
   lsof -i :9090
   # Kill process if needed: kill -9 <PID>
   ```

2. **Check volume permissions**:
   ```bash
   sudo chmod -R 777 prometheus_data/
   sudo chown -R 65534:65534 prometheus_data/  # Prometheus user
   ```

3. **View detailed logs**:
   ```bash
   docker-compose -f docker-compose-monitoring.yml logs prometheus
   ```

4. **Rebuild containers**:
   ```bash
   docker-compose -f docker-compose-monitoring.yml down
   docker volume prune
   docker-compose -f docker-compose-monitoring.yml up -d
   ```

### Issue 2: "Grafana login fails"
**Error**: Cannot login with admin/admin

**Solutions**:
1. **Default credentials**:
   - Username: `admin`
   - Password: `admin`
   - First login will prompt to change password

2. **Grafana won't start**:
   ```bash
   docker logs ai-grafana
   # Check for port conflicts
   lsof -i :3000
   ```

3. **Forgot password**:
   ```bash
   # Reset in container
   docker exec ai-grafana grafana-cli admin reset-admin-password newpassword
   ```

4. **Check datasource connection**:
   - Go to Configuration → Datasources
   - Edit Prometheus
   - Verify URL: `http://prometheus:9090`
   - Click "Test"

### Issue 3: "Prometheus metrics scrape failing"
**Error**: Targets showing RED in Prometheus UI

**Diagnosis**:
```bash
# Visit http://localhost:9090/targets
# Should show:
# - flask-api ... UP
# - node-exporter ... UP
```

**Solutions**:
1. **Verify API is running**:
   ```bash
   curl http://localhost:5000/metrics
   # Should return Prometheus metrics text
   ```

2. **Check Prometheus config**:
   ```yaml
   # In prometheus.yml
   scrape_configs:
     - job_name: 'flask-api'
       static_configs:
         - targets: ['localhost:5000']  # Not 'api:5000' in docker
       metrics_path: '/metrics'
   ```

3. **For Docker Compose deployment**:
   ```yaml
   # In docker-compose-monitoring.yml
   scrape_configs:
     - job_name: 'flask-api'
       static_configs:
         - targets: ['api:5000']  # Use service name
   ```

4. **Restart Prometheus**:
   ```bash
   docker-compose -f docker-compose-monitoring.yml restart prometheus
   ```

### Issue 4: "Grafana dashboard empty (no data)"
**Error**: Dashboard panels show "No data"

**Solutions**:
1. **Verify Prometheus has data**:
   ```
   Visit http://localhost:9090
   Graph tab
   Query: model_accuracy
   Should return metric name suggestions
   ```

2. **Check metric names in dashboard**:
   ```json
   {
     "targets": [
       {
         "expr": "model_accuracy{model_name=\"churn_model\"}"
       }
     ]
   }
   ```

3. **Wait for first scrape**:
   - Prometheus needs ~5-10 seconds to scrape first metrics
   - Restart API if no metrics after 30 seconds

4. **Check data is being generated**:
   ```bash
   curl http://localhost:5000/metrics | grep -i "model_"
   # Should show metrics like: model_accuracy 0.87
   ```

### Issue 5: "Alerts not firing"
**Error**: Thresholds exceeded but no alerts

**Diagnosis**:
```
1. Visit http://localhost:9090/alerts
2. Check "Alerting rules"
3. Look for red "FIRING" alerts
```

**Solutions**:
1. **Verify alert rules syntax**:
   ```bash
   # Validate YAML
   yaml-lint alerting_rules.yml
   ```

2. **Check alert rule expression**:
   ```yaml
   alert: ModelAccuracyLow
   expr: model_accuracy{model_name="churn_model"} < 0.80
   # Make sure metric exists
   ```

3. **Ensure Alertmanager is running**:
   ```bash
   curl http://localhost:9093/
   # Should return Alertmanager UI HTML
   ```

4. **Check Alertmanager routing**:
   ```yaml
   # In alertmanager.yml
   route:
     receiver: 'default'
   receivers:
     - name: 'default'
       webhook_configs:
         - url: 'http://localhost:5001/alerts'
   ```

### Issue 6: "Slack notifications not arriving"
**Error**: Alerts fire but Slack is silent

**Solutions**:
1. **Configure Slack webhook**:
   ```yaml
   # In alertmanager.yml
   global:
     slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   ```

2. **Test Slack webhook**:
   ```bash
   curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
     -H 'Content-type: application/json' \
     -d '{"text":"Test message"}'
   ```

3. **Restart Alertmanager**:
   ```bash
   docker-compose -f docker-compose-monitoring.yml restart alertmanager
   ```

4. **Check Alertmanager logs**:
   ```bash
   docker logs ai-alertmanager
   ```

---

## General Troubleshooting

### All services failing
**Issue**: Nothing working, multiple failures

**Recovery Steps**:
```bash
# 1. Stop everything
docker-compose -f docker-compose-monitoring.yml down
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# 2. Clear volumes
docker volume prune

# 3. Rebuild everything
docker-compose -f docker-compose-monitoring.yml up -d

# 4. Validate
python validate_setup.py
```

### Port already in use
**Error**: "Address already in use" for port XXXX

**Solutions**:
```bash
# Find what's using the port
lsof -i :3000  # For port 3000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
# "3000:3000" → "3001:3000"
```

### Memory/resource issues
**Error**: Services restart, Docker OOM

**Solutions**:
```bash
# Increase Docker memory limit
# Docker Desktop → Preferences → Resources → Memory: 4GB+

# Or reduce Prometheus retention
# In prometheus.yml
# --storage.tsdb.retention.time=7d
```

### File permissions issues
**Error**: "Permission denied" when accessing volumes

**Solutions**:
```bash
# Fix permissions
sudo chmod -R 777 prometheus_data/
sudo chmod -R 777 grafana_data/
sudo chmod -R 777 alertmanager_data/

# Or use sudo with docker-compose
sudo docker-compose -f docker-compose-monitoring.yml up -d
```

---

## Logs & Debugging

### View Logs
```bash
# All services
docker-compose -f docker-compose-monitoring.yml logs -f

# Specific service
docker-compose -f docker-compose-monitoring.yml logs -f prometheus
docker-compose -f docker-compose-monitoring.yml logs -f grafana
docker-compose -f docker-compose-monitoring.yml logs -f alertmanager

# Flask API
tail -f backend/logs/app.log

# Browser console
F12 → Console tab
```

### Enable Debug Mode
```python
# In phase5_api_server.py
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Check Service Health
```bash
# Flask API
curl http://localhost:5000/api/v1/models/status

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health

# Alertmanager
curl http://localhost:9093/-/healthy
```

---

## Common Fixes Checklist

When things don't work, try these in order:

- [ ] Run `python validate_setup.py`
- [ ] Check all services are running
- [ ] Review service logs
- [ ] Check port conflicts
- [ ] Verify API endpoints respond
- [ ] Check database connection
- [ ] Clear browser cache
- [ ] Restart Docker containers
- [ ] Rebuild Docker images
- [ ] Check firewall rules
- [ ] Verify environment variables

---

## Still Stuck?

### Check Documentation
- Full guide: `TASKS_A_B_C_IMPLEMENTATION.md`
- Architecture: `ARCHITECTURE_OVERVIEW.md`
- Quick start: `README_TASKS_ABC.md`

### Manual Testing
```bash
# Test API
curl http://localhost:5000/api/v1/models/status

# Test Prometheus scrape
curl http://localhost:9090/api/v1/query?query=up

# Test Grafana datasource
curl http://localhost:3000/api/datasources

# Test metrics export
curl http://localhost:5000/metrics
```

### Contact Support
- Check GitHub issues
- Review Flask/Prometheus/Grafana documentation
- Look at Docker logs
- Validate setup with `validate_setup.py`

---

## Prevention Tips

1. **Always run `validate_setup.py` after changes**
2. **Keep Docker containers updated**: `docker-compose pull`
3. **Monitor disk space**: Large metric files can fill disk
4. **Regular backups**: Volume data survives container restarts
5. **Check logs regularly**: Catch issues early
6. **Test in development first**: Before deploying to production

---

**Last Updated**: January 1, 2024
**For Latest Help**: Run `python validate_setup.py`
