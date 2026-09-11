"""
Model Monitoring and Drift Detection System
=============================================
Tracks ML model performance, detects data drift, and triggers automatic retraining.

Features:
- Real-time accuracy tracking
- Statistical drift detection (Kolmogorov-Smirnov test)
- Model performance comparison
- Automatic retraining recommendations
- Historical metrics logging
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from scipy import stats
from typing import Dict, List, Tuple, Any
import pickle
from collections import deque

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/model_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelMetrics:
    """Stores and manages model performance metrics."""
    
    def __init__(self, model_name: str, max_history: int = 1000):
        self.model_name = model_name
        self.max_history = max_history
        
        # Metric tracking
        self.predictions = deque(maxlen=max_history)
        self.actuals = deque(maxlen=max_history)
        self.confidences = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        
        # Accuracy tracking
        self.accuracy_history = deque(maxlen=100)
        self.precision_history = deque(maxlen=100)
        self.recall_history = deque(maxlen=100)
        self.f1_history = deque(maxlen=100)
        
        # Performance metrics
        self.latency_history = deque(maxlen=1000)
        self.error_count = 0
        self.total_predictions = 0
        
        logger.info(f"Initialized metrics for model: {model_name}")
    
    def record_prediction(self, prediction: Any, actual: Any = None, 
                         confidence: float = None, latency: float = None):
        """Record a single prediction and optional actual value."""
        self.predictions.append(prediction)
        if actual is not None:
            self.actuals.append(actual)
        if confidence is not None:
            self.confidences.append(confidence)
        if latency is not None:
            self.latency_history.append(latency)
        
        self.timestamps.append(datetime.now())
        self.total_predictions += 1
    
    def calculate_accuracy(self) -> float:
        """Calculate accuracy based on correct predictions."""
        if len(self.actuals) == 0:
            return 0.0
        
        correct = sum(1 for p, a in zip(self.predictions, self.actuals) if p == a)
        return correct / len(self.actuals)
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        if len(self.actuals) == 0:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0
            }
        
        accuracy = self.calculate_accuracy()
        
        # For regression models, use RMSE instead
        if self._is_regression():
            predictions_arr = np.array(list(self.predictions))
            actuals_arr = np.array(list(self.actuals))
            mse = np.mean((predictions_arr - actuals_arr) ** 2)
            rmse = np.sqrt(mse)
            
            return {
                'accuracy': accuracy,
                'rmse': rmse,
                'mae': np.mean(np.abs(predictions_arr - actuals_arr)),
                'r2': 1 - (np.sum((actuals_arr - predictions_arr) ** 2) / 
                          np.sum((actuals_arr - np.mean(actuals_arr)) ** 2))
            }
        
        # Classification metrics
        tp = sum(1 for p, a in zip(self.predictions, self.actuals) if p == 1 and a == 1)
        fp = sum(1 for p, a in zip(self.predictions, self.actuals) if p == 1 and a == 0)
        fn = sum(1 for p, a in zip(self.predictions, self.actuals) if p == 0 and a == 1)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    def _is_regression(self) -> bool:
        """Detect if this is a regression model."""
        if len(self.predictions) == 0:
            return False
        
        sample = self.predictions[0]
        return isinstance(sample, (int, float)) and not isinstance(sample, bool)
    
    def get_average_latency(self) -> float:
        """Get average prediction latency."""
        if len(self.latency_history) == 0:
            return 0.0
        return np.mean(list(self.latency_history))
    
    def get_p95_latency(self) -> float:
        """Get 95th percentile latency."""
        if len(self.latency_history) == 0:
            return 0.0
        return np.percentile(list(self.latency_history), 95)
    
    def get_error_rate(self) -> float:
        """Get error rate percentage."""
        if self.total_predictions == 0:
            return 0.0
        return (self.error_count / self.total_predictions) * 100


class DriftDetector:
    """Detects data drift using statistical tests."""
    
    @staticmethod
    def kolmogorov_smirnov_test(baseline: np.ndarray, current: np.ndarray, 
                               threshold: float = 0.05) -> Tuple[bool, float]:
        """
        Kolmogorov-Smirnov test for detecting drift.
        
        Returns:
            (drift_detected, p_value)
        """
        if len(baseline) == 0 or len(current) == 0:
            return False, 1.0
        
        statistic, p_value = stats.ks_2samp(baseline, current)
        drift_detected = p_value < threshold
        
        return drift_detected, p_value
    
    @staticmethod
    def wasserstein_distance(baseline: np.ndarray, current: np.ndarray,
                            threshold: float = 0.1) -> Tuple[bool, float]:
        """
        Wasserstein distance for detecting distribution shift.
        
        Returns:
            (drift_detected, distance)
        """
        if len(baseline) == 0 or len(current) == 0:
            return False, 0.0
        
        distance = stats.wasserstein_distance(baseline, current)
        drift_detected = distance > threshold
        
        return drift_detected, distance
    
    @staticmethod
    def population_stability_index(baseline: np.ndarray, current: np.ndarray,
                                  threshold: float = 0.1) -> Tuple[bool, float]:
        """
        Population Stability Index for detecting categorical drift.
        
        Returns:
            (drift_detected, psi)
        """
        if len(baseline) == 0 or len(current) == 0:
            return False, 0.0
        
        # Bin the data
        bins = np.histogram_bin_edges(
            np.concatenate([baseline, current]), 
            bins=10
        )
        
        baseline_counts = np.histogram(baseline, bins=bins)[0]
        current_counts = np.histogram(current, bins=bins)[0]
        
        # Normalize
        baseline_pct = baseline_counts / len(baseline)
        current_pct = current_counts / len(current)
        
        # Avoid log(0)
        baseline_pct = np.where(baseline_pct == 0, 1e-10, baseline_pct)
        current_pct = np.where(current_pct == 0, 1e-10, current_pct)
        
        psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
        drift_detected = psi > threshold
        
        return drift_detected, psi


class ModelMonitor:
    """Main model monitoring orchestrator."""
    
    def __init__(self, models_dir: str = './models', history_dir: str = './monitoring_history'):
        self.models_dir = Path(models_dir)
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        
        # Model metrics storage
        self.model_metrics: Dict[str, ModelMetrics] = {}
        
        # Configuration
        self.retraining_thresholds = {
            'accuracy_drop': 0.05,  # 5% drop triggers retraining
            'error_rate': 0.05,     # 5% error rate
            'drift_threshold': 0.05,  # KS test p-value
        }
        
        logger.info(f"Initialized ModelMonitor with models_dir={models_dir}")
    
    def register_model(self, model_name: str, max_history: int = 1000):
        """Register a model for monitoring."""
        if model_name not in self.model_metrics:
            self.model_metrics[model_name] = ModelMetrics(model_name, max_history)
            logger.info(f"Registered model for monitoring: {model_name}")
    
    def record_prediction(self, model_name: str, prediction: Any, 
                         actual: Any = None, confidence: float = None,
                         latency: float = None):
        """Record a prediction from a model."""
        if model_name not in self.model_metrics:
            self.register_model(model_name)
        
        self.model_metrics[model_name].record_prediction(
            prediction, actual, confidence, latency
        )
    
    def get_model_health(self, model_name: str) -> Dict[str, Any]:
        """Get comprehensive health report for a model."""
        if model_name not in self.model_metrics:
            return {}
        
        metrics = self.model_metrics[model_name]
        performance = metrics.calculate_metrics()
        
        health_report = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat(),
            'performance': performance,
            'latency': {
                'average_ms': metrics.get_average_latency() * 1000,
                'p95_ms': metrics.get_p95_latency() * 1000
            },
            'predictions': {
                'total': metrics.total_predictions,
                'error_rate': metrics.get_error_rate()
            }
        }
        
        return health_report
    
    def check_drift(self, model_name: str, baseline_data: np.ndarray,
                   current_data: np.ndarray) -> Dict[str, Any]:
        """Check for data drift in model input features."""
        detector = DriftDetector()
        
        ks_drift, ks_pvalue = detector.kolmogorov_smirnov_test(
            baseline_data, current_data,
            threshold=self.retraining_thresholds['drift_threshold']
        )
        
        wd_drift, wd_value = detector.wasserstein_distance(
            baseline_data, current_data
        )
        
        psi_drift, psi_value = detector.population_stability_index(
            baseline_data, current_data
        )
        
        drift_report = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {
                'kolmogorov_smirnov': {
                    'drift_detected': ks_drift,
                    'p_value': float(ks_pvalue)
                },
                'wasserstein_distance': {
                    'drift_detected': wd_drift,
                    'distance': float(wd_value)
                },
                'population_stability_index': {
                    'drift_detected': psi_drift,
                    'psi': float(psi_value)
                }
            },
            'overall_drift': ks_drift or wd_drift or psi_drift
        }
        
        return drift_report
    
    def check_retraining_needed(self, model_name: str, 
                               baseline_accuracy: float = None) -> Dict[str, Any]:
        """Check if model needs retraining."""
        if model_name not in self.model_metrics:
            return {'needs_retraining': False, 'reasons': []}
        
        metrics = self.model_metrics[model_name]
        performance = metrics.calculate_metrics()
        reasons = []
        
        # Check accuracy drop
        if baseline_accuracy and 'accuracy' in performance:
            accuracy_drop = baseline_accuracy - performance['accuracy']
            if accuracy_drop > self.retraining_thresholds['accuracy_drop']:
                reasons.append(
                    f"Accuracy dropped by {accuracy_drop*100:.2f}% "
                    f"(from {baseline_accuracy*100:.2f}% to {performance['accuracy']*100:.2f}%)"
                )
        
        # Check error rate
        error_rate = metrics.get_error_rate()
        if error_rate > self.retraining_thresholds['error_rate'] * 100:
            reasons.append(f"Error rate is {error_rate:.2f}%")
        
        return {
            'model_name': model_name,
            'needs_retraining': len(reasons) > 0,
            'reasons': reasons,
            'current_accuracy': performance.get('accuracy', 0.0),
            'error_rate': error_rate
        }
    
    def save_history(self, model_name: str, report: Dict[str, Any]):
        """Save monitoring report to history."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.history_dir / f"{model_name}_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Saved monitoring report to {filename}")
    
    def get_all_models_status(self) -> List[Dict[str, Any]]:
        """Get status of all monitored models."""
        status_list = []
        for model_name in self.model_metrics.keys():
            health = self.get_model_health(model_name)
            status_list.append(health)
        return status_list
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'models': self.get_all_models_status(),
            'summary': {
                'total_models': len(self.model_metrics),
                'total_predictions': sum(
                    m.total_predictions for m in self.model_metrics.values()
                ),
                'average_error_rate': np.mean([
                    m.get_error_rate() for m in self.model_metrics.values()
                ]) if self.model_metrics else 0.0
            }
        }
        return report


# Convenience functions for integration with Flask API

def get_model_monitor() -> ModelMonitor:
    """Get or create global model monitor instance."""
    global _model_monitor
    if '_model_monitor' not in globals():
        _model_monitor = ModelMonitor()
    return _model_monitor


def record_prediction(model_name: str, prediction: Any, actual: Any = None,
                     confidence: float = None, latency: float = None):
    """Record a prediction in the global monitor."""
    monitor = get_model_monitor()
    monitor.record_prediction(model_name, prediction, actual, confidence, latency)


def get_model_health(model_name: str) -> Dict[str, Any]:
    """Get health report for a specific model."""
    monitor = get_model_monitor()
    return monitor.get_model_health(model_name)


def get_all_models_status() -> List[Dict[str, Any]]:
    """Get status of all monitored models."""
    monitor = get_model_monitor()
    return monitor.get_all_models_status()


if __name__ == '__main__':
    # Example usage
    monitor = ModelMonitor()
    
    # Register models
    monitor.register_model('churn_model')
    monitor.register_model('revenue_model')
    
    # Simulate predictions
    print("Simulating predictions...")
    for i in range(100):
        # Churn predictions (binary)
        churn_pred = np.random.choice([0, 1])
        churn_actual = np.random.choice([0, 1])
        monitor.record_prediction('churn_model', churn_pred, churn_actual, 
                                 confidence=np.random.random(), latency=np.random.random()*0.1)
        
        # Revenue predictions (continuous)
        revenue_pred = np.random.normal(500, 100)
        revenue_actual = np.random.normal(500, 100)
        monitor.record_prediction('revenue_model', revenue_pred, revenue_actual, 
                                 latency=np.random.random()*0.05)
    
    # Generate reports
    print("\nModel Health Reports:")
    for model in monitor.get_all_models_status():
        print(f"\n{model['model_name']}:")
        print(f"  Accuracy: {model['performance'].get('accuracy', 0)*100:.2f}%")
        print(f"  Avg Latency: {model['latency']['average_ms']:.2f}ms")
        print(f"  Error Rate: {model['predictions']['error_rate']:.2f}%")
    
    # Check drift
    print("\n\nDrift Detection Example:")
    baseline = np.random.normal(0, 1, 100)
    current = np.random.normal(0.5, 1, 100)  # Shifted distribution
    
    drift_report = monitor.check_drift('churn_model', baseline, current)
    print(f"Drift detected: {drift_report['overall_drift']}")
    print(f"KS test p-value: {drift_report['tests']['kolmogorov_smirnov']['p_value']:.4f}")
