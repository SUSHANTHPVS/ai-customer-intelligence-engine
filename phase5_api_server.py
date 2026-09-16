#!/usr/bin/env python3
"""
PHASE 5: API Server for ML Model Predictions
================================================

REST API server for serving real-time predictions from Phase 4 trained models.
Exposes endpoints for churn, revenue, engagement, and segmentation predictions.

Architecture:
- Flask web framework with CORS support
- Model loading from pickle files with caching
- Database integration for customer data
- Request validation and error handling
- Comprehensive logging and monitoring

Author: AI Customer Intelligence Engine
Date: 2026-09-09
"""

import os
import sys
import pickle
import logging
import traceback
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps
import json

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flasgger import Swagger
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
from psycopg2.extras import RealDictCursor
from sklearn.preprocessing import StandardScaler, LabelEncoder

from cache import cached, get_redis
from extensions import limiter
from auth import auth_bp, init_auth_db
from customers_bp import customers_bp
from jobs import jobs_bp, start_scheduler
from export_bp import export_bp
from realtime import socketio, start_emitter
from admin_bp import admin_bp, init_admin_db, verify_api_key
from audit import init_audit_db, record_audit
from twofa import twofa_bp, init_2fa_columns
from webhooks_bp import webhooks_bp, init_webhooks_db
from import_bp import import_bp
from graphql_bp import graphql_bp
from insights import insights_bp
from datasets_bp import datasets_bp, init_datasets_db, get_active_dataset_id
from ml_bp import ml_bp, train_churn_model, analyze_model_drift
from cohort_bp import cohort_bp


def _dataset_cache_key():
    """Cache key variant so analytics responses never leak across datasets/tenants."""
    try:
        return get_active_dataset_id(get_jwt_identity())
    except Exception:
        return 'default'

# ==================== CONFIGURATION ====================

# Create Flask app
app = Flask(__name__)
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:9000,http://localhost:5173').split(',')
CORS(app, origins=[origin.strip() for origin in cors_origins if origin.strip()])

# Limit upload size (dataset CSV uploads) to prevent resource-exhaustion abuse
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# JWT authentication
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)


@jwt.token_in_blocklist_loader
def _check_if_token_revoked(jwt_header, jwt_payload):
    return get_redis().exists(f"revoked_token:{jwt_payload['jti']}") == 1


# Redis-backed rate limiting (protects login/register from brute force)
app.config['RATELIMIT_STORAGE_URI'] = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}"
limiter.init_app(app)

# OpenAPI/Swagger docs at /api/docs
app.config['SWAGGER'] = {
    'title': 'Customer Intelligence API',
    'uiversion': 3,
    'specs_route': '/api/docs/',
}
Swagger(app, template={
    'info': {
        'title': 'AI Customer Intelligence Engine API',
        'description': 'ML predictions, analytics, customer 360 search and real-time monitoring',
        'version': '2.0.0',
    }
})

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(export_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(twofa_bp)
app.register_blueprint(webhooks_bp)
app.register_blueprint(import_bp)
app.register_blueprint(graphql_bp)
app.register_blueprint(insights_bp)
app.register_blueprint(datasets_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(cohort_bp)

# Real-time WebSocket support
socketio.init_app(app)

# Prometheus metrics at /metrics (request counts, latencies, etc.)
metrics = PrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'AI Customer Intelligence Engine API', version='2.0.0')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}

# Model configuration
MODEL_DIR = 'models'
MODEL_FILES = {
    'churn': f'{MODEL_DIR}/churn_model.pkl',
    'churn_scaler': f'{MODEL_DIR}/churn_scaler.pkl',
    'engagement': f'{MODEL_DIR}/engagement_model.pkl',
    'engagement_scaler': f'{MODEL_DIR}/engagement_scaler.pkl',
    'revenue': f'{MODEL_DIR}/revenue_model.pkl',
    'revenue_scaler': f'{MODEL_DIR}/revenue_scaler.pkl',
    'segmentation': f'{MODEL_DIR}/segmentation_model.pkl',
    'segmentation_scaler': f'{MODEL_DIR}/segmentation_scaler.pkl',
}

ENCODER_FILES = {
    'churn_country': f'{MODEL_DIR}/encoder_churn_country.pkl',
    'churn_industry': f'{MODEL_DIR}/encoder_churn_industry.pkl',
    'churn_acquisition_channel': f'{MODEL_DIR}/encoder_churn_acquisition_channel.pkl',
    'engagement_country': f'{MODEL_DIR}/encoder_engagement_country.pkl',
    'engagement_industry': f'{MODEL_DIR}/encoder_engagement_industry.pkl',
    'engagement_acquisition_channel': f'{MODEL_DIR}/encoder_engagement_acquisition_channel.pkl',
    'engagement_rfm_segment': f'{MODEL_DIR}/encoder_engagement_rfm_segment.pkl',
    'engagement_subscription_plan': f'{MODEL_DIR}/encoder_engagement_subscription_plan.pkl',
}

# ==================== MODEL LOADER ====================

class ModelManager:
    """Manages loading and caching of ML models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.loaded = False
        
    def load_all_models(self) -> bool:
        """Load all models from disk"""
        logger.info("[API Server] Loading ML models...")
        
        try:
            # Load models
            for model_name, filepath in MODEL_FILES.items():
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    logger.info(f"  ✓ Loaded {model_name}")
                else:
                    logger.error(f"  ✗ Model file not found: {filepath}")
                    return False
            
            # Load encoders if they exist (will use LabelEncoder on-demand if not)
            for encoder_name, filepath in ENCODER_FILES.items():
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        self.encoders[encoder_name] = pickle.load(f)
                    logger.info(f"  ✓ Loaded encoder {encoder_name}")
            
            self.loaded = True
            logger.info("[API Server] ✓ All models loaded successfully\n")
            return True
            
        except Exception as e:
            logger.error(f"[API Server] ✗ Failed to load models: {e}")
            return False
    
    def get_model(self, model_name: str) -> Any:
        """Get model by name"""
        return self.models.get(model_name)
    
    def get_scaler(self, scaler_name: str) -> Any:
        """Get scaler by name"""
        return self.models.get(scaler_name)
    
    def get_encoder(self, encoder_name: str) -> Any:
        """Get encoder by name"""
        return self.encoders.get(encoder_name)

# Global model manager
model_manager = ModelManager()

# ==================== DATABASE CONNECTION ====================

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def query_customer_data(customer_id: str) -> Dict[str, Any]:
    """Query customer data from database - MUST include all columns used during Phase 4 training"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # CRITICAL: This query MUST match columns from Phase 4 training (phase4_setup.py load_features)
        query = """
        SELECT 
            c.customer_id,
            c.country,
            c.industry,
            c.acquisition_channel,
            rf.rfm_score,
            rf.rfm_segment,
            rf.recency_days,
            rf.frequency_transactions,
            rf.monetary_value,
            bh.total_events,
            bh.unique_event_types,
            bh.unique_features_used,
            bh.avg_session_duration,
            bh.login_frequency,
            bh.feature_usage_premium_pct,
            en.engagement_score,
            en.days_since_signup,
            en.days_active,
            en.is_active_last_30days::INT,
            en.is_active_last_7days::INT,
            rv.total_revenue,
            rv.subscription_plan,
            rv.avg_transaction_value,
            rv.transaction_frequency,
            rv.failed_payment_count,
            rv.subscription_tenure_days,
            sp.total_tickets,
            sp.avg_resolution_hours,
            sp.avg_satisfaction_score,
            sp.critical_priority_count,
            sp.issue_resolution_rate,
            cr.churn_risk_score,
            cr.churn_risk_category,
            cr.days_inactive
        FROM customers c
        LEFT JOIN feature_rfm rf ON c.customer_id = rf.customer_id
        LEFT JOIN feature_behavioral bh ON c.customer_id = bh.customer_id
        LEFT JOIN feature_engagement en ON c.customer_id = en.customer_id
        LEFT JOIN feature_revenue rv ON c.customer_id = rv.customer_id
        LEFT JOIN feature_support sp ON c.customer_id = sp.customer_id
        LEFT JOIN feature_churn_risk cr ON c.customer_id = cr.customer_id
        WHERE c.customer_id = %s
        """
        
        cur.execute(query, (customer_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Failed to query customer data: {e}")
        return None

# ==================== REQUEST/RESPONSE UTILITIES ====================

def require_api_key(f):
    """Decorator to check API key against the admin-issued key store"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        if not verify_api_key(api_key):
            return jsonify({'error': 'Invalid or revoked API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(f):
    """Decorator for error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

# ==================== PREDICTION UTILITIES ====================

def prepare_churn_features(data: Dict[str, Any]) -> np.ndarray:
    """Prepare features for churn prediction - MUST match Phase 4 training"""
    # Exclude same columns as Phase 4: 'customer_id', 'churn_risk_category', 'churn_risk_score', 
    # 'rfm_segment', 'subscription_plan', 'activity_trend'
    excluded_cols = {'customer_id', 'churn_risk_category', 'churn_risk_score', 
                     'rfm_segment', 'subscription_plan', 'activity_trend'}
    
    # DON'T filter out None values - we'll fill them properly
    feature_cols = [col for col in data.keys() if col not in excluded_cols]
    
    try:
        X = pd.DataFrame([data])[feature_cols]
        
        # Fill missing values
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if X[col].isna().any():
                X[col] = X[col].fillna(0)
        
        categorical_cols = ['country', 'industry', 'acquisition_channel']
        for col in categorical_cols:
            if col in X.columns and X[col].isna().any():
                X[col] = X[col].fillna('Unknown')
        
        # Encode categoricals
        for col in categorical_cols:
            if col in X.columns:
                encoder = model_manager.get_encoder(f'churn_{col}')
                if encoder:
                    try:
                        X[col] = encoder.transform(X[col].astype(str))
                    except ValueError:
                        # Handle unknown categories
                        X[col] = 0
                else:
                    X[col] = 0
        
        # Scale
        scaler = model_manager.get_scaler('churn_scaler')
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values
        
        return X_scaled
    except Exception as e:
        logger.error(f"Error preparing churn features: {e}")
        raise ValueError(f"Cannot prepare features for churn prediction: {str(e)}")

def prepare_engagement_features(data: Dict[str, Any]) -> np.ndarray:
    """Prepare features for engagement prediction - MUST match Phase 4 training"""
    # Exclude same columns as Phase 4
    excluded_cols = {'customer_id', 'engagement_score', 'days_since_signup', 'days_active',
                     'is_active_last_30days', 'is_active_last_7days', 'activity_trend',
                     'churn_risk_category', 'churn_risk_score'}
    
    # DON'T filter out None values - we'll fill them properly
    feature_cols = [col for col in data.keys() if col not in excluded_cols]
    
    try:
        X = pd.DataFrame([data])[feature_cols]
        
        # Fill missing values
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if X[col].isna().any():
                X[col] = X[col].fillna(0)
        
        categorical_cols = ['country', 'industry', 'acquisition_channel', 'rfm_segment', 'subscription_plan']
        for col in categorical_cols:
            if col in X.columns and X[col].isna().any():
                X[col] = X[col].fillna('Unknown')
        
        # Encode categoricals
        for col in categorical_cols:
            if col in X.columns:
                encoder = model_manager.get_encoder(f'engagement_{col}')
                if encoder:
                    try:
                        X[col] = encoder.transform(X[col].astype(str))
                    except ValueError:
                        X[col] = 0
                else:
                    X[col] = 0
        
        # Scale
        scaler = model_manager.get_scaler('engagement_scaler')
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values
        
        return X_scaled
    except Exception as e:
        logger.error(f"Error preparing engagement features: {e}")
        raise ValueError(f"Cannot prepare features for engagement prediction: {str(e)}")

def prepare_revenue_features(data: Dict[str, Any]) -> np.ndarray:
    """Prepare features for revenue prediction - MUST match Phase 4 training"""
    # Phase 4 uses ONLY these 6 columns for revenue model
    feature_cols = ['rfm_score', 'engagement_score', 'frequency_transactions',
                   'login_frequency', 'days_active', 'subscription_tenure_days']
    
    try:
        X = pd.DataFrame([data])[feature_cols]
        
        # Fill missing values with 0
        for col in feature_cols:
            if col in X.columns and X[col].isna().any():
                X[col] = X[col].fillna(0)
        
        # Scale
        scaler = model_manager.get_scaler('revenue_scaler')
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values
        
        return X_scaled
    except Exception as e:
        logger.error(f"Error preparing revenue features: {e}")
        raise ValueError(f"Cannot prepare features for revenue prediction: {str(e)}")

# ==================== API ROUTES ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        redis_ok = get_redis().ping()
    except Exception:
        redis_ok = False

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': model_manager.loaded,
        'redis_connected': redis_ok,
    }), 200

@app.route('/api/v1/predict/churn', methods=['POST'])
@require_api_key
@handle_errors
def predict_churn():
    """
    Predict churn risk for a customer
    
    Request JSON:
    {
        "customer_id": "C000001",
        "features": {...}  // Optional: provide features directly
    }
    
    Response:
    {
        "customer_id": "C000001",
        "churn_probability": 0.95,
        "churn_prediction": 1,
        "risk_level": "HIGH",
        "timestamp": "2026-09-09T..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    
    # Get customer features
    customer_data = query_customer_data(customer_id)
    if not customer_data:
        return jsonify({'error': f'Customer not found: {customer_id}'}), 404
    
    # Prepare features
    X_scaled = prepare_churn_features(customer_data)
    
    # Predict
    model = model_manager.get_model('churn')
    churn_prob = model.predict_proba(X_scaled)[0, 1]
    churn_pred = model.predict(X_scaled)[0]
    
    # Determine risk level
    if churn_prob >= 0.8:
        risk_level = 'CRITICAL'
    elif churn_prob >= 0.6:
        risk_level = 'HIGH'
    elif churn_prob >= 0.4:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return jsonify({
        'customer_id': customer_id,
        'churn_probability': float(churn_prob),
        'churn_prediction': int(churn_pred),
        'risk_level': risk_level,
        'timestamp': datetime.now().isoformat(),
        'model_version': '1.0'
    }), 200

@app.route('/api/v1/predict/engagement', methods=['POST'])
@require_api_key
@handle_errors
def predict_engagement():
    """
    Predict engagement score for a customer
    
    Request JSON:
    {
        "customer_id": "C000001"
    }
    
    Response:
    {
        "customer_id": "C000001",
        "engagement_score": 85.5,
        "engagement_level": "HIGH",
        "timestamp": "2026-09-09T..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    
    # Get customer features
    customer_data = query_customer_data(customer_id)
    if not customer_data:
        return jsonify({'error': f'Customer not found: {customer_id}'}), 404
    
    # Prepare features
    X_scaled = prepare_engagement_features(customer_data)
    
    # Predict
    model = model_manager.get_model('engagement')
    engagement_score = model.predict(X_scaled)[0]
    engagement_score = np.clip(engagement_score, 0, 100)  # Ensure 0-100 range
    
    # Determine engagement level
    if engagement_score >= 80:
        engagement_level = 'VERY HIGH'
    elif engagement_score >= 60:
        engagement_level = 'HIGH'
    elif engagement_score >= 40:
        engagement_level = 'MEDIUM'
    elif engagement_score >= 20:
        engagement_level = 'LOW'
    else:
        engagement_level = 'VERY LOW'
    
    return jsonify({
        'customer_id': customer_id,
        'engagement_score': float(engagement_score),
        'engagement_level': engagement_level,
        'timestamp': datetime.now().isoformat(),
        'model_version': '1.0'
    }), 200

@app.route('/api/v1/predict/revenue', methods=['POST'])
@require_api_key
@handle_errors
def predict_revenue():
    """
    Predict revenue for a customer
    
    Request JSON:
    {
        "customer_id": "C000001"
    }
    
    Response:
    {
        "customer_id": "C000001",
        "revenue_forecast": 1250.50,
        "revenue_bracket": "HIGH",
        "timestamp": "2026-09-09T..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    
    # Get customer features
    customer_data = query_customer_data(customer_id)
    if not customer_data:
        return jsonify({'error': f'Customer not found: {customer_id}'}), 404
    
    # Prepare features
    X_scaled = prepare_revenue_features(customer_data)
    
    # Predict
    model = model_manager.get_model('revenue')
    revenue_forecast = model.predict(X_scaled)[0]
    revenue_forecast = max(0, revenue_forecast)  # Ensure non-negative
    
    # Determine revenue bracket
    if revenue_forecast >= 1500:
        revenue_bracket = 'VERY HIGH'
    elif revenue_forecast >= 1000:
        revenue_bracket = 'HIGH'
    elif revenue_forecast >= 500:
        revenue_bracket = 'MEDIUM'
    elif revenue_forecast >= 200:
        revenue_bracket = 'LOW'
    else:
        revenue_bracket = 'MINIMAL'
    
    return jsonify({
        'customer_id': customer_id,
        'revenue_forecast': float(revenue_forecast),
        'revenue_bracket': revenue_bracket,
        'timestamp': datetime.now().isoformat(),
        'model_version': '1.0'
    }), 200

@app.route('/api/v1/predict/segment', methods=['POST'])
@require_api_key
@handle_errors
def predict_segment():
    """
    Get customer segment/cluster
    
    Request JSON:
    {
        "customer_id": "C000001"
    }
    
    Response:
    {
        "customer_id": "C000001",
        "cluster": 0,
        "segment_name": "VIP",
        "description": "High-value, highly engaged customer",
        "timestamp": "2026-09-09T..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    
    # Get customer features
    customer_data = query_customer_data(customer_id)
    if not customer_data:
        return jsonify({'error': f'Customer not found: {customer_id}'}), 404
    
    # Prepare features for segmentation
    feature_cols = ['rfm_score', 'engagement_score', 'total_revenue', 
                    'login_frequency', 'days_active']
    X = pd.DataFrame([customer_data])[feature_cols]
    X = X.fillna(X.median())
    
    # Scale
    scaler = model_manager.get_scaler('segmentation_scaler')
    X_scaled = scaler.transform(X)
    
    # Predict
    model = model_manager.get_model('segmentation')
    cluster = model.predict(X_scaled)[0]
    
    # Map cluster to segment name
    segment_map = {
        0: {'name': 'STANDARD', 'description': 'Regular customers with normal engagement'},
        1: {'name': 'DORMANT', 'description': 'Inactive customers, at risk of churn'},
        2: {'name': 'AT_RISK', 'description': 'Disengaged customers requiring attention'},
        3: {'name': 'VIP', 'description': 'High-value, highly engaged customers'}
    }
    
    segment_info = segment_map.get(cluster, {'name': 'UNKNOWN', 'description': 'Unknown segment'})
    
    return jsonify({
        'customer_id': customer_id,
        'cluster': int(cluster),
        'segment_name': segment_info['name'],
        'description': segment_info['description'],
        'timestamp': datetime.now().isoformat(),
        'model_version': '1.0'
    }), 200

@app.route('/api/v1/predict/batch', methods=['POST'])
@require_api_key
@handle_errors
def predict_batch():
    """
    Get all predictions for a customer (churn, revenue, engagement, segment)
    
    Request JSON:
    {
        "customer_id": "C000001"
    }
    
    Response:
    {
        "customer_id": "C000001",
        "churn": {...},
        "revenue": {...},
        "engagement": {...},
        "segment": {...},
        "timestamp": "2026-09-09T..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    
    # Get customer features
    customer_data = query_customer_data(customer_id)
    if not customer_data:
        return jsonify({'error': f'Customer not found: {customer_id}'}), 404
    
    # Get all predictions
    churn_payload = {'customer_id': customer_id}
    churn_result = predict_churn_internal(customer_data)
    
    revenue_result = predict_revenue_internal(customer_data)
    
    engagement_result = predict_engagement_internal(customer_data)
    
    segment_result = predict_segment_internal(customer_data)
    
    return jsonify({
        'customer_id': customer_id,
        'churn': churn_result,
        'revenue': revenue_result,
        'engagement': engagement_result,
        'segment': segment_result,
        'timestamp': datetime.now().isoformat()
    }), 200

def predict_churn_internal(customer_data: Dict) -> Dict:
    """Internal churn prediction"""
    X_scaled = prepare_churn_features(customer_data)
    model = model_manager.get_model('churn')
    churn_prob = float(model.predict_proba(X_scaled)[0, 1])
    churn_pred = int(model.predict(X_scaled)[0])
    
    if churn_prob >= 0.8:
        risk_level = 'CRITICAL'
    elif churn_prob >= 0.6:
        risk_level = 'HIGH'
    elif churn_prob >= 0.4:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return {
        'churn_probability': churn_prob,
        'churn_prediction': churn_pred,
        'risk_level': risk_level
    }

def predict_revenue_internal(customer_data: Dict) -> Dict:
    """Internal revenue prediction"""
    X_scaled = prepare_revenue_features(customer_data)
    model = model_manager.get_model('revenue')
    revenue_forecast = float(max(0, model.predict(X_scaled)[0]))
    
    if revenue_forecast >= 1500:
        revenue_bracket = 'VERY HIGH'
    elif revenue_forecast >= 1000:
        revenue_bracket = 'HIGH'
    elif revenue_forecast >= 500:
        revenue_bracket = 'MEDIUM'
    elif revenue_forecast >= 200:
        revenue_bracket = 'LOW'
    else:
        revenue_bracket = 'MINIMAL'
    
    return {
        'revenue_forecast': revenue_forecast,
        'revenue_bracket': revenue_bracket
    }

def predict_engagement_internal(customer_data: Dict) -> Dict:
    """Internal engagement prediction"""
    X_scaled = prepare_engagement_features(customer_data)
    model = model_manager.get_model('engagement')
    engagement_score = float(np.clip(model.predict(X_scaled)[0], 0, 100))
    
    if engagement_score >= 80:
        engagement_level = 'VERY HIGH'
    elif engagement_score >= 60:
        engagement_level = 'HIGH'
    elif engagement_score >= 40:
        engagement_level = 'MEDIUM'
    elif engagement_score >= 20:
        engagement_level = 'LOW'
    else:
        engagement_level = 'VERY LOW'
    
    return {
        'engagement_score': engagement_score,
        'engagement_level': engagement_level
    }

def predict_segment_internal(customer_data: Dict) -> Dict:
    """Internal segment prediction"""
    feature_cols = ['rfm_score', 'engagement_score', 'total_revenue', 
                    'login_frequency', 'days_active']
    X = pd.DataFrame([customer_data])[feature_cols]
    X = X.fillna(X.median())
    
    scaler = model_manager.get_scaler('segmentation_scaler')
    X_scaled = scaler.transform(X)
    
    model = model_manager.get_model('segmentation')
    cluster = int(model.predict(X_scaled)[0])
    
    segment_map = {
        0: {'name': 'STANDARD', 'description': 'Regular customers with normal engagement'},
        1: {'name': 'DORMANT', 'description': 'Inactive customers, at risk of churn'},
        2: {'name': 'AT_RISK', 'description': 'Disengaged customers requiring attention'},
        3: {'name': 'VIP', 'description': 'High-value, highly engaged customers'}
    }
    
    segment_info = segment_map.get(cluster, {'name': 'UNKNOWN', 'description': 'Unknown segment'})
    
    return {
        'cluster': cluster,
        'segment_name': segment_info['name'],
        'description': segment_info['description']
    }

@app.route('/api/v1/models/status', methods=['GET'])
def model_status():
    """Get status of all loaded models"""
    status = {
        'models_loaded': model_manager.loaded,
        'models': list(model_manager.models.keys()),
        'scalers': list(model_manager.scalers.keys()),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status), 200

# ==================== ANALYTICS ENDPOINTS ====================

@app.route('/analytics/customer-segmentation', methods=['GET'])
@jwt_required()
@cached('analytics:customer-segmentation', ttl=60, vary_by=_dataset_cache_key)
def get_customer_segmentation():
    """Get customer segmentation distribution"""
    try:
        dataset_id = get_active_dataset_id(get_jwt_identity())
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        WITH total_customers AS (
            SELECT COUNT(*) as total FROM feature_engagement WHERE dataset_id = %s
        )
        SELECT 
            segment,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT total FROM total_customers), 1) as percentage
        FROM feature_engagement
        WHERE dataset_id = %s
        GROUP BY segment
        ORDER BY count DESC
        """
        
        cur.execute(query, (dataset_id, dataset_id))
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'segments': [dict(row) for row in results],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching customer segmentation: {e}")
        return jsonify({'segments': [], 'timestamp': datetime.now().isoformat()}), 200

@app.route('/analytics/engagement-metrics', methods=['GET'])
@jwt_required()
@cached('analytics:engagement-metrics', ttl=60, vary_by=_dataset_cache_key)
def get_engagement_metrics():
    """Get engagement metrics"""
    try:
        dataset_id = get_active_dataset_id(get_jwt_identity())
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            ROUND(AVG(engagement_score), 2) as avg_engagement,
            ROUND(MAX(engagement_score), 2) as max_engagement,
            ROUND(MIN(engagement_score), 2) as min_engagement,
            ROUND(STDDEV(engagement_score), 2) as stddev_engagement,
            COUNT(*) as total_customers,
            SUM(CASE WHEN active_days_last_30 > 0 THEN 1 ELSE 0 END) as active_30days,
            ROUND(AVG(active_days_last_30), 2) as avg_active_days,
            ROUND(AVG(feature_usage_count), 2) as avg_feature_usage
        FROM feature_engagement
        WHERE dataset_id = %s
        """
        
        cur.execute(query, (dataset_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        metrics = dict(result) if result else {}
        metrics['timestamp'] = datetime.now().isoformat()
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error fetching engagement metrics: {e}")
        return jsonify({'timestamp': datetime.now().isoformat()}), 200

@app.route('/analytics/ltv-predictions', methods=['GET'])
@jwt_required()
@cached('analytics:ltv-predictions', ttl=60, vary_by=_dataset_cache_key)
def get_ltv_predictions():
    """Get LTV predictions vs actual"""
    try:
        dataset_id = get_active_dataset_id(get_jwt_identity())
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            ROUND(AVG(rf.lifetime_value), 2) as actual_ltv,
            ROUND(AVG(rf.predicted_ltv), 2) as predicted_ltv,
            COUNT(*) as customer_count,
            ROUND(AVG(rf.frequency), 2) as avg_frequency,
            ROUND(AVG(rf.monetary), 2) as avg_monetary
        FROM feature_rfm rf
        WHERE rf.dataset_id = %s
        """
        
        cur.execute(query, (dataset_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        ltv_data = dict(result) if result else {}
        ltv_data['timestamp'] = datetime.now().isoformat()
        
        return jsonify(ltv_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching LTV predictions: {e}")
        return jsonify({'timestamp': datetime.now().isoformat()}), 200

@app.route('/analytics/churn-risk', methods=['GET'])
@jwt_required()
@cached('analytics:churn-risk', ttl=60, vary_by=_dataset_cache_key)
def get_churn_risk():
    """Get churn risk analysis"""
    try:
        dataset_id = get_active_dataset_id(get_jwt_identity())
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            risk_level,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM feature_churn_risk WHERE dataset_id = %s), 1) as percentage
        FROM feature_churn_risk
        WHERE dataset_id = %s
        GROUP BY risk_level
        ORDER BY CASE 
            WHEN risk_level = 'HIGH' THEN 1
            WHEN risk_level = 'MEDIUM' THEN 2
            WHEN risk_level = 'LOW' THEN 3
            ELSE 4
        END
        """
        
        cur.execute(query, (dataset_id, dataset_id))
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'churn_risk': [dict(row) for row in results],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching churn risk: {e}")
        return jsonify({'churn_risk': [], 'timestamp': datetime.now().isoformat()}), 200

@app.route('/models/metrics', methods=['GET'])
@jwt_required()
def get_model_metrics():
    """Get model performance metrics for the active dataset."""
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT model_metrics FROM datasets WHERE id = %s",
            (dataset_id,)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    metrics = row['model_metrics'] if row and row.get('model_metrics') else {
        'model_name': 'churn_model',
        'accuracy': 0.0,
        'precision': 0.0,
        'recall': 0.0,
        'f1_score': 0.0,
        'trained_at': None,
        'drift': {'overall_drift': False, 'feature_tests': []},
        'retraining_scheduled': False,
    }

    if not row or not row.get('model_metrics'):
        try:
            metrics = train_churn_model(dataset_id)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE datasets SET model_metrics = %s WHERE id = %s", (json.dumps(metrics), dataset_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Model metrics fallback training failed for {dataset_id}: {e}")

    return jsonify({
        'dataset_id': dataset_id,
        **metrics,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/models/leaderboard', methods=['GET'])
@jwt_required()
def get_model_leaderboard():
    """Return a leaderboard for all trained models and per-model comparison."""
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, model_metrics FROM datasets WHERE status = 'ready' ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    leaderboard = []
    for row in rows:
        metrics = row.get('model_metrics') or {}
        leaderboard.append({
            'dataset_id': row['id'],
            'dataset_name': row['name'],
            'model_name': metrics.get('model_name', 'churn_model'),
            'accuracy': metrics.get('accuracy', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'f1_score': metrics.get('f1_score', 0),
            'drift_detected': bool(metrics.get('drift', {}).get('overall_drift', False)),
            'trained_at': metrics.get('trained_at'),
        })

    leaderboard.sort(key=lambda m: (m['f1_score'], m['precision'], m['recall'], m['accuracy']), reverse=True)
    return jsonify({
        'leaderboard': leaderboard,
        'dataset_id': dataset_id,
        'timestamp': datetime.now().isoformat(),
    }), 200


@app.route('/models/<model_name>/retrain', methods=['POST'])
@jwt_required()
def run_model_retrain(model_name):
    """Manually retrain a model for the active dataset."""
    dataset_id = get_active_dataset_id(get_jwt_identity())
    try:
        metrics = train_churn_model(dataset_id)
        if 'error' in metrics:
            return jsonify(metrics), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE datasets SET model_metrics = %s WHERE id = %s", (json.dumps(metrics), dataset_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'dataset_id': dataset_id,
            'status': 'retrained',
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"Manual retrain failed for dataset {dataset_id}: {e}")
        return jsonify({'error': 'Retraining failed'}), 500


@app.route('/models/performance', methods=['GET'])
@jwt_required()
def get_model_performance():
    """Get historical model performance trends."""
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT model_metrics FROM datasets WHERE id = %s",
            (dataset_id,)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    metrics = row['model_metrics'] if row and row.get('model_metrics') else None
    history = []
    if metrics:
        history.append({
            'date': metrics.get('trained_at') or datetime.now().isoformat(),
            'accuracy': metrics.get('accuracy', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'f1_score': metrics.get('f1_score', 0),
            'drift_detected': bool(metrics.get('drift', {}).get('overall_drift', False)),
        })

    return jsonify({
        'performance_history': history,
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("PHASE 5: ML MODEL PREDICTION API SERVER")
    logger.info("=" * 70)
    
    # Load models
    if not model_manager.load_all_models():
        logger.error("Failed to load models. Exiting.")
        sys.exit(1)

    # Initialize auth (users table + default admin) and background services
    try:
        init_auth_db()
        init_audit_db()
        init_admin_db()
        init_2fa_columns()
        init_webhooks_db()
        init_datasets_db()
    except Exception as e:
        logger.error(f"[Auth] Failed to initialize auth/admin database: {e}")

    start_scheduler()
    start_emitter()
    
    # Start Flask server
    logger.info("\n[API Server] Starting Flask API server...")
    logger.info("[API Server] Available endpoints:")
    logger.info("  POST /api/v1/predict/churn")
    logger.info("  POST /api/v1/predict/revenue")
    logger.info("  POST /api/v1/predict/engagement")
    logger.info("  POST /api/v1/predict/segment")
    logger.info("  POST /api/v1/predict/batch")
    logger.info("  GET  /api/v1/models/status")
    logger.info("  POST /auth/register, /auth/login, /auth/refresh, /auth/logout")
    logger.info("  POST /auth/2fa/setup, /auth/2fa/enable, /auth/2fa/login-verify")
    logger.info("  GET  /customers/search, /customers/<id>/profile")
    logger.info("  POST /customers/import (CSV bulk upload)")
    logger.info("  GET  /export/customers.csv, /export/analytics-report.csv, /export/analytics-report.pdf")
    logger.info("  GET  /jobs/status")
    logger.info("  GET  /analytics/insights (automated insights)")
    logger.info("  ANY  /admin/webhooks")
    logger.info("  POST /graphql")
    logger.info("  GET  /api/docs (Swagger UI)")
    logger.info("  WS   /socket.io (live risk_alert feed)")
    logger.info("  GET  /health")
    server_port = int(os.getenv('PORT', 5000))
    logger.info(f"\n[API Server] Server running on port {server_port}\n")
    
    # Run server (SocketIO wraps the Werkzeug dev server for WebSocket support)
    socketio.run(
        app,
        host='0.0.0.0',
        port=server_port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )

