#!/usr/bin/env python3
"""
Per-dataset ML model training.

Trains a real scikit-learn RandomForest classifier on each dataset's own
engineered features (RFM, behavioral, engagement, revenue, support) to
predict churn risk, producing genuine held-out accuracy/precision/recall/F1
metrics instead of the static demo numbers shown for the pre-trained models.
"""
import base64
import logging
import pickle
from datetime import datetime, timezone

import numpy as np
from psycopg2.extras import RealDictCursor, Json
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler

from audit import get_db_connection, record_audit
from cache import cache_set

logger = logging.getLogger(__name__)
ml_bp = Blueprint('ml', __name__, url_prefix='/datasets')

FEATURE_COLUMNS = [
    'recency', 'frequency', 'monetary', 'avg_session_duration', 'login_frequency',
    'engagement_score', 'active_days_last_30', 'feature_usage_count',
    'total_revenue', 'total_tickets', 'avg_resolution_time'
]
MIN_TRAINING_ROWS = 20

ANOMALY_FEATURE_COLUMNS = [
    'recency', 'frequency', 'monetary', 'avg_session_duration', 'login_frequency',
    'engagement_score', 'active_days_last_30', 'total_revenue', 'total_tickets'
]
MIN_ANOMALY_ROWS = 20


def _load_training_frame(dataset_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                fr.customer_id,
                COALESCE(fr.recency, 0) as recency,
                COALESCE(fr.frequency, 0) as frequency,
                COALESCE(fr.monetary, 0) as monetary,
                COALESCE(fb.avg_session_duration, 0) as avg_session_duration,
                COALESCE(fb.login_frequency, 0) as login_frequency,
                COALESCE(fe.engagement_score, 0) as engagement_score,
                COALESCE(fe.active_days_last_30, 0) as active_days_last_30,
                COALESCE(fe.feature_usage_count, 0) as feature_usage_count,
                COALESCE(frev.total_revenue, 0) as total_revenue,
                COALESCE(fs.total_tickets, 0) as total_tickets,
                COALESCE(fs.avg_resolution_time, 0) as avg_resolution_time,
                fc.risk_level
            FROM feature_rfm fr
            LEFT JOIN feature_behavioral fb ON fr.customer_id = fb.customer_id AND fb.dataset_id = %s
            LEFT JOIN feature_engagement fe ON fr.customer_id = fe.customer_id AND fe.dataset_id = %s
            LEFT JOIN feature_revenue frev ON fr.customer_id = frev.customer_id AND frev.dataset_id = %s
            LEFT JOIN feature_support fs ON fr.customer_id = fs.customer_id AND fs.dataset_id = %s
            LEFT JOIN feature_churn_risk fc ON fr.customer_id = fc.customer_id AND fc.dataset_id = %s
            WHERE fr.dataset_id = %s
        """, (dataset_id,) * 6)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def train_churn_model(dataset_id):
    """Train + evaluate a churn classifier for one dataset; returns a metrics dict."""
    rows = _load_training_frame(dataset_id)
    if len(rows) < MIN_TRAINING_ROWS:
        return {'error': f'Need at least {MIN_TRAINING_ROWS} customers to train a model (found {len(rows)})'}

    X = np.array([[float(r[c]) for c in FEATURE_COLUMNS] for r in rows])
    y = np.array([1 if r['risk_level'] == 'HIGH' else 0 for r in rows])

    if len(set(y.tolist())) < 2:
        return {'error': 'Dataset needs both HIGH and non-HIGH risk customers to train a classifier'}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, class_weight='balanced')
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)

    feature_importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_.tolist()),
        key=lambda pair: pair[1], reverse=True
    )

    metrics = {
        'accuracy': round(float(accuracy_score(y_test, y_pred)), 4),
        'precision': round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        'f1_score': round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        'training_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'feature_importances': [{'feature': f, 'importance': round(i, 4)} for f, i in feature_importances],
        'trained_at': datetime.now(timezone.utc).isoformat(),
    }

    bundle = pickle.dumps({'model': model, 'scaler': scaler})
    cache_set(f'ml_model:{dataset_id}:churn', base64.b64encode(bundle).decode('ascii'), ttl=86400)

    return metrics


@ml_bp.route('/<dataset_id>/train', methods=['POST'])
@jwt_required()
def train_dataset_model(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id FROM datasets WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        if not cur.fetchone():
            return jsonify({'error': 'Dataset not found'}), 404
    finally:
        cur.close()
        conn.close()

    result = train_churn_model(dataset_id)
    if 'error' in result:
        return jsonify(result), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE datasets SET model_metrics = %s WHERE id = %s", (Json(result), dataset_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'dataset_model_trained', f"id={dataset_id} accuracy={result['accuracy']}")
    return jsonify(result), 200


@ml_bp.route('/<dataset_id>/model', methods=['GET'])
@jwt_required()
def get_dataset_model(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT model_metrics FROM datasets WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        return jsonify({'error': 'Dataset not found'}), 404
    return jsonify({'model_metrics': row['model_metrics']}), 200


def _load_anomaly_frame(dataset_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                c.customer_id, c.first_name, c.last_name,
                COALESCE(fr.recency, 0) as recency,
                COALESCE(fr.frequency, 0) as frequency,
                COALESCE(fr.monetary, 0) as monetary,
                COALESCE(fb.avg_session_duration, 0) as avg_session_duration,
                COALESCE(fb.login_frequency, 0) as login_frequency,
                COALESCE(fe.engagement_score, 0) as engagement_score,
                COALESCE(fe.active_days_last_30, 0) as active_days_last_30,
                COALESCE(frev.total_revenue, 0) as total_revenue,
                COALESCE(fs.total_tickets, 0) as total_tickets
            FROM customers c
            LEFT JOIN feature_rfm fr ON fr.customer_id = c.customer_id AND fr.dataset_id = c.dataset_id
            LEFT JOIN feature_behavioral fb ON fb.customer_id = c.customer_id AND fb.dataset_id = c.dataset_id
            LEFT JOIN feature_engagement fe ON fe.customer_id = c.customer_id AND fe.dataset_id = c.dataset_id
            LEFT JOIN feature_revenue frev ON frev.customer_id = c.customer_id AND frev.dataset_id = c.dataset_id
            LEFT JOIN feature_support fs ON fs.customer_id = c.customer_id AND fs.dataset_id = c.dataset_id
            WHERE c.dataset_id = %s
        """, (dataset_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def detect_anomalies(dataset_id, contamination=0.05):
    """Flags customers whose behavior/revenue pattern deviates sharply from the dataset's norm."""
    rows = _load_anomaly_frame(dataset_id)
    if len(rows) < MIN_ANOMALY_ROWS:
        return {'error': f'Need at least {MIN_ANOMALY_ROWS} customers to detect anomalies (found {len(rows)})'}

    X = np.array([[float(r[c]) for c in ANOMALY_FEATURE_COLUMNS] for r in rows])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    labels = model.fit_predict(X_scaled)
    raw_scores = model.decision_function(X_scaled)

    anomalies = []
    for i, label in enumerate(labels):
        if label == -1:
            r = rows[i]
            anomalies.append({
                'customer_id': r['customer_id'],
                'name': f"{r['first_name']} {r['last_name']}".strip() or r['customer_id'],
                'anomaly_score': round(float(-raw_scores[i]), 4),
                'recency': int(r['recency']),
                'frequency': int(r['frequency']),
                'monetary': round(float(r['monetary']), 2),
                'total_revenue': round(float(r['total_revenue']), 2),
                'engagement_score': round(float(r['engagement_score']), 2),
            })

    anomalies.sort(key=lambda a: a['anomaly_score'], reverse=True)
    anomalies = anomalies[:50]

    return {
        'total_customers': len(rows),
        'anomaly_count': len(anomalies),
        'anomaly_rate_pct': round(len(anomalies) / len(rows) * 100, 2) if rows else 0,
        'anomalies': anomalies,
        'detected_at': datetime.now(timezone.utc).isoformat(),
    }


@ml_bp.route('/<dataset_id>/detect-anomalies', methods=['POST'])
@jwt_required()
def detect_dataset_anomalies(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id FROM datasets WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        if not cur.fetchone():
            return jsonify({'error': 'Dataset not found'}), 404
    finally:
        cur.close()
        conn.close()

    result = detect_anomalies(dataset_id)
    if 'error' in result:
        return jsonify(result), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE datasets SET anomaly_report = %s WHERE id = %s", (Json(result), dataset_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'dataset_anomalies_detected', f"id={dataset_id} count={result['anomaly_count']}")
    return jsonify(result), 200


@ml_bp.route('/<dataset_id>/anomalies', methods=['GET'])
@jwt_required()
def get_dataset_anomalies(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT anomaly_report FROM datasets WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        return jsonify({'error': 'Dataset not found'}), 404
    return jsonify({'anomaly_report': row['anomaly_report']}), 200
