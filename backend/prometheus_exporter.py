"""
Prometheus Metrics Exporter for ML Models
==========================================
Exports model performance metrics in Prometheus format for monitoring and alerting.

Provides metrics for:
- API request/response metrics
- Model inference latency
- Model accuracy and performance
- Error rates
- Prediction volumes
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Callable
from functools import wraps
from collections import defaultdict
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
from prometheus_client.core import REGISTRY

logger = logging.getLogger(__name__)

# Create custom registry for our metrics
metrics_registry = CollectorRegistry()

# ============================================================================
# API Metrics
# ============================================================================

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=metrics_registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    registry=metrics_registry
)

# ============================================================================
# Model Prediction Metrics
# ============================================================================

predictions_total = Counter(
    'model_predictions_total',
    'Total predictions made by model',
    ['model_name'],
    registry=metrics_registry
)

prediction_latency_seconds = Histogram(
    'model_prediction_latency_seconds',
    'Model prediction latency in seconds',
    ['model_name'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=metrics_registry
)

prediction_errors_total = Counter(
    'model_prediction_errors_total',
    'Total prediction errors',
    ['model_name'],
    registry=metrics_registry
)

model_accuracy = Gauge(
    'model_accuracy',
    'Model accuracy score',
    ['model_name'],
    registry=metrics_registry
)

model_precision = Gauge(
    'model_precision',
    'Model precision score',
    ['model_name'],
    registry=metrics_registry
)

model_recall = Gauge(
    'model_recall',
    'Model recall score',
    ['model_name'],
    registry=metrics_registry
)

model_f1_score = Gauge(
    'model_f1_score',
    'Model F1 score',
    ['model_name'],
    registry=metrics_registry
)

# ============================================================================
# Churn Model Metrics
# ============================================================================

churn_predictions = Counter(
    'churn_predictions_total',
    'Total churn predictions',
    registry=metrics_registry
)

churn_risk_distribution = Gauge(
    'churn_risk_high_count',
    'Number of high-risk churn predictions',
    registry=metrics_registry
)

# ============================================================================
# Revenue Model Metrics
# ============================================================================

revenue_predictions = Counter(
    'revenue_predictions_total',
    'Total revenue predictions',
    registry=metrics_registry
)

revenue_forecast_sum = Counter(
    'revenue_forecast_sum',
    'Sum of all revenue forecasts',
    registry=metrics_registry
)

# ============================================================================
# Engagement Model Metrics
# ============================================================================

engagement_predictions = Counter(
    'engagement_predictions_total',
    'Total engagement predictions',
    registry=metrics_registry
)

engagement_score_average = Gauge(
    'engagement_score_average',
    'Average engagement score',
    registry=metrics_registry
)

# ============================================================================
# Segmentation Model Metrics
# ============================================================================

segmentation_predictions = Counter(
    'segmentation_predictions_total',
    'Total segmentation predictions',
    registry=metrics_registry
)

vip_customers_count = Gauge(
    'vip_customers_count',
    'Number of VIP customers identified',
    registry=metrics_registry
)

# ============================================================================
# Data Drift Metrics
# ============================================================================

data_drift_detected = Gauge(
    'data_drift_detected',
    'Data drift detection flag (1=drift detected, 0=no drift)',
    ['model_name'],
    registry=metrics_registry
)

data_drift_score = Gauge(
    'data_drift_score',
    'Data drift detection score',
    ['model_name'],
    registry=metrics_registry
)

# ============================================================================
# System Metrics
# ============================================================================

database_connection_errors = Counter(
    'database_connection_errors_total',
    'Total database connection errors',
    registry=metrics_registry
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=metrics_registry
)

api_server_status = Gauge(
    'api_server_status',
    'API server status (1=up, 0=down)',
    registry=metrics_registry
)

# ============================================================================
# Retraining Metrics
# ============================================================================

retraining_total = Counter(
    'model_retraining_total',
    'Total model retrainings',
    ['model_name'],
    registry=metrics_registry
)

retraining_duration_seconds = Histogram(
    'model_retraining_duration_seconds',
    'Model retraining duration in seconds',
    ['model_name'],
    buckets=(1, 5, 10, 30, 60, 300, 600),
    registry=metrics_registry
)

# ============================================================================
# Decorators and Utility Functions
# ============================================================================

def track_api_request(method: str, endpoint: str):
    """Decorator to track API request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            http_requests_in_progress.inc()
            start_time = time.time()
            status = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_in_progress.dec()
                http_request_duration_seconds.labels(method, endpoint).observe(duration)
                
                # Extract status from result if it's a tuple with status code
                if isinstance(result, tuple) and len(result) > 1:
                    if isinstance(result[1], int):
                        status = result[1]
                
                http_requests_total.labels(method, endpoint, status).inc()
        
        return wrapper
    return decorator


def track_model_prediction(model_name: str):
    """Decorator to track model prediction metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                predictions_total.labels(model_name).inc()
                prediction_latency_seconds.labels(model_name).observe(duration)
                
                return result
            except Exception as e:
                prediction_errors_total.labels(model_name).inc()
                raise
        
        return wrapper
    return decorator


def track_database_query(func: Callable) -> Callable:
    """Decorator to track database query metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            database_connection_errors.inc()
            raise
        finally:
            duration = time.time() - start_time
            database_query_duration_seconds.observe(duration)
    
    return wrapper


# ============================================================================
# Metric Update Functions
# ============================================================================

def update_model_accuracy(model_name: str, accuracy: float):
    """Update model accuracy metric."""
    model_accuracy.labels(model_name).set(accuracy)


def update_model_precision(model_name: str, precision: float):
    """Update model precision metric."""
    model_precision.labels(model_name).set(precision)


def update_model_recall(model_name: str, recall: float):
    """Update model recall metric."""
    model_recall.labels(model_name).set(recall)


def update_model_f1(model_name: str, f1_score: float):
    """Update model F1 score metric."""
    model_f1_score.labels(model_name).set(f1_score)


def record_churn_prediction(risk_level: str):
    """Record churn prediction metrics."""
    churn_predictions.inc()
    if risk_level in ['HIGH', 'CRITICAL']:
        churn_risk_distribution.set(churn_risk_distribution._value.get() + 1)


def record_revenue_prediction(revenue_amount: float):
    """Record revenue prediction metrics."""
    revenue_predictions.inc()
    revenue_forecast_sum.inc(revenue_amount)


def record_engagement_prediction(engagement_score: float):
    """Record engagement prediction metrics."""
    engagement_predictions.inc()
    engagement_score_average.set(engagement_score)


def record_segmentation_prediction(segment_name: str):
    """Record segmentation prediction metrics."""
    segmentation_predictions.inc()
    if segment_name == 'VIP':
        vip_customers_count.set(vip_customers_count._value.get() + 1)


def set_drift_detected(model_name: str, detected: bool, score: float = None):
    """Set data drift detection metrics."""
    data_drift_detected.labels(model_name).set(1 if detected else 0)
    if score is not None:
        data_drift_score.labels(model_name).set(score)


def record_retraining(model_name: str, duration: float):
    """Record model retraining event."""
    retraining_total.labels(model_name).inc()
    retraining_duration_seconds.labels(model_name).observe(duration)


def set_api_server_status(status: int):
    """Set API server status (1=up, 0=down)."""
    api_server_status.set(status)


# ============================================================================
# Export Functions
# ============================================================================

def get_metrics_text() -> str:
    """Get all metrics in Prometheus text format."""
    return generate_latest(metrics_registry).decode('utf-8')


def get_metrics_dict() -> Dict[str, List[Dict[str, Any]]]:
    """Get all metrics as a dictionary structure."""
    metrics_data = {}
    
    for collector in metrics_registry._collector_to_names:
        for metric in collector.collect():
            metrics_data[metric.name] = []
            
            for sample in metric.samples:
                metrics_data[metric.name].append({
                    'name': sample.name,
                    'labels': sample.labels,
                    'value': sample.value,
                    'timestamp': sample.timestamp
                })
    
    return metrics_data


class MetricsCollector:
    """Collects and aggregates metrics for reporting."""
    
    def __init__(self):
        self.prediction_times = defaultdict(list)
        self.prediction_counts = defaultdict(int)
        self.errors = defaultdict(int)
    
    def record_prediction_time(self, model_name: str, duration: float):
        """Record prediction time for a model."""
        self.prediction_times[model_name].append(duration)
        self.prediction_counts[model_name] += 1
    
    def record_error(self, model_name: str):
        """Record error for a model."""
        self.errors[model_name] += 1
    
    def get_statistics(self, model_name: str) -> Dict[str, float]:
        """Get statistics for a model."""
        if model_name not in self.prediction_times or not self.prediction_times[model_name]:
            return {}
        
        times = self.prediction_times[model_name]
        
        return {
            'count': self.prediction_counts[model_name],
            'avg_latency': np.mean(times),
            'p50_latency': np.percentile(times, 50),
            'p95_latency': np.percentile(times, 95),
            'p99_latency': np.percentile(times, 99),
            'min_latency': np.min(times),
            'max_latency': np.max(times),
            'error_count': self.errors[model_name]
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all models."""
        return {
            model_name: self.get_statistics(model_name)
            for model_name in self.prediction_counts.keys()
        }


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    return _metrics_collector


if __name__ == '__main__':
    # Example usage
    print("Prometheus Metrics Export Example")
    print("=" * 50)
    
    # Simulate some metrics
    update_model_accuracy('churn_model', 0.87)
    update_model_precision('churn_model', 0.89)
    update_model_recall('churn_model', 0.85)
    update_model_f1('churn_model', 0.87)
    
    predictions_total.labels('churn_model').inc(100)
    prediction_latency_seconds.labels('churn_model').observe(0.05)
    
    set_drift_detected('churn_model', True, 0.15)
    
    # Output metrics in Prometheus format
    print(get_metrics_text())
