#!/usr/bin/env python3
"""
Real-time monitoring feed over WebSockets (Flask-SocketIO).
Broadcasts simulated live churn-risk alerts to connected dashboard
clients, scoped per-dataset via Socket.IO rooms so each user only ever
sees activity from their own active dataset.
"""
import logging
import os
import threading
import time
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import request as flask_request
from flask_jwt_extended import decode_token
from flask_socketio import SocketIO, join_room

logger = logging.getLogger(__name__)
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:9000,http://localhost:5173').split(',')
socketio = SocketIO(
    cors_allowed_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    async_mode="threading",
)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}

_emitter_started = False
_emitter_lock = threading.Lock()

# Tracks how many connected clients are watching each dataset room
_room_counts = {}
_sid_dataset = {}
_room_lock = threading.Lock()


def _fetch_random_risk_customer(dataset_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT customer_id, churn_risk_score, risk_level
            FROM feature_churn_risk
            WHERE dataset_id = %s
            ORDER BY RANDOM()
            LIMIT 1
        """, (dataset_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def _background_emitter():
    logger.info("[Realtime] Live monitoring feed started")
    while True:
        try:
            with _room_lock:
                dataset_ids = list(_room_counts.keys())

            for dataset_id in dataset_ids:
                row = _fetch_random_risk_customer(dataset_id)
                if not row:
                    continue
                alert = {
                    'customer_id': row['customer_id'],
                    'risk_level': row['risk_level'],
                    'churn_risk_score': float(row['churn_risk_score']) if row['churn_risk_score'] is not None else None,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
                socketio.emit('risk_alert', alert, room=dataset_id)
                if alert['risk_level'] == 'HIGH':
                    _notify_webhooks(alert, dataset_id)
        except Exception as e:
            logger.warning(f"[Realtime] emitter error: {e}")
        time.sleep(8)


def _notify_webhooks(alert, dataset_id):
    try:
        from webhooks_bp import dispatch_risk_alert_webhooks
        dispatch_risk_alert_webhooks({**alert, 'dataset_id': dataset_id})
    except Exception as e:
        logger.warning(f"[Realtime] webhook dispatch failed: {e}")


def start_emitter():
    global _emitter_started
    with _emitter_lock:
        if _emitter_started:
            return
        _emitter_started = True
    thread = threading.Thread(target=_background_emitter, daemon=True)
    thread.start()


def _resolve_dataset_id(auth):
    """Determine which dataset room a connecting client should join from its JWT."""
    token = None
    if isinstance(auth, dict):
        token = auth.get('token')
    if not token:
        token = flask_request.args.get('token')

    if not token:
        return 'default'

    try:
        decoded = decode_token(token)
        username = decoded.get('sub')
        from datasets_bp import get_active_dataset_id
        return get_active_dataset_id(username)
    except Exception as e:
        logger.warning(f"[Realtime] Could not resolve dataset from token: {e}")
        return 'default'


@socketio.on('connect')
def handle_connect(auth=None):
    dataset_id = _resolve_dataset_id(auth)
    sid = flask_request.sid

    join_room(dataset_id)
    _sid_dataset[sid] = dataset_id
    with _room_lock:
        _room_counts[dataset_id] = _room_counts.get(dataset_id, 0) + 1

    logger.info(f"[Realtime] Client connected (dataset={dataset_id})")
    socketio.emit('connected', {'message': 'Connected to live monitoring feed', 'dataset_id': dataset_id}, room=sid)


@socketio.on('disconnect')
def handle_disconnect():
    sid = flask_request.sid
    dataset_id = _sid_dataset.pop(sid, None)
    if dataset_id:
        with _room_lock:
            remaining = _room_counts.get(dataset_id, 1) - 1
            if remaining <= 0:
                _room_counts.pop(dataset_id, None)
            else:
                _room_counts[dataset_id] = remaining
    logger.info("[Realtime] Client disconnected")



@socketio.on('disconnect')
def handle_disconnect():
    logger.info("[Realtime] Client disconnected")
