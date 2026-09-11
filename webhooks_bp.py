#!/usr/bin/env python3
"""
Outbound webhook integrations. Admins register HTTPS endpoints that
receive HMAC-signed JSON payloads whenever a HIGH churn-risk event
fires, enabling integration with external systems (Slack, CRM, etc.).
"""
import hashlib
import hmac
import json
import logging
import secrets

import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from psycopg2.extras import RealDictCursor

from rbac import role_required
from audit import get_db_connection, record_audit

logger = logging.getLogger(__name__)
webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/admin/webhooks')


def init_webhooks_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id SERIAL PRIMARY KEY,
                url VARCHAR(500) NOT NULL,
                secret VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) DEFAULT 'risk_alert.high',
                active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                last_triggered_at TIMESTAMP,
                last_status VARCHAR(255)
            )
        """)
        cur.execute("ALTER TABLE webhooks ALTER COLUMN last_status TYPE VARCHAR(255)")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def deliver_webhook(hook, payload):
    """POST a signed JSON payload to a webhook URL and record delivery status."""
    body = json.dumps(payload).encode('utf-8')
    signature = hmac.new(hook['secret'].encode('utf-8'), body, hashlib.sha256).hexdigest()

    try:
        resp = requests.post(
            hook['url'],
            data=body,
            headers={'Content-Type': 'application/json', 'X-Signature-SHA256': signature},
            timeout=5
        )
        status = str(resp.status_code)
        ok = resp.ok
    except Exception as e:
        status = f"error: {e}"
        ok = False
        logger.warning(f"[Webhooks] Delivery to {hook['url']} failed: {e}")

    status = status[:255]

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE webhooks SET last_triggered_at = NOW(), last_status = %s WHERE id = %s",
            (status, hook['id'])
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return ok


def dispatch_risk_alert_webhooks(alert_payload):
    """Fan out a HIGH risk alert to every active registered webhook."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM webhooks WHERE active = TRUE AND event_type = 'risk_alert.high'")
        hooks = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    for hook in hooks:
        deliver_webhook(hook, {'event': 'risk_alert.high', 'data': alert_payload})


@webhooks_bp.route('', methods=['POST'])
@role_required('admin')
def create_webhook():
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url.startswith('http'):
        return jsonify({'error': 'A valid http(s) URL is required'}), 400

    secret = secrets.token_hex(16)
    username = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """INSERT INTO webhooks (url, secret, created_by)
               VALUES (%s, %s, %s) RETURNING id, url, secret, event_type, active, created_at""",
            (url, secret, username)
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'webhook_created', f"id={row['id']} url={url}")
    return jsonify(row), 201


@webhooks_bp.route('', methods=['GET'])
@role_required('admin')
def list_webhooks():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, url, event_type, active, created_by, created_at, last_triggered_at, last_status
            FROM webhooks ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return jsonify({'webhooks': rows}), 200


@webhooks_bp.route('/<int:webhook_id>', methods=['DELETE'])
@role_required('admin')
def delete_webhook(webhook_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM webhooks WHERE id = %s", (webhook_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'webhook_deleted', f"id={webhook_id}")
    return jsonify({'message': 'Webhook deleted'}), 200


@webhooks_bp.route('/<int:webhook_id>/test', methods=['POST'])
@role_required('admin')
def test_webhook(webhook_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM webhooks WHERE id = %s", (webhook_id,))
        hook = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not hook:
        return jsonify({'error': 'Webhook not found'}), 404

    delivered = deliver_webhook(hook, {'event': 'test', 'message': 'This is a test payload from Customer Intelligence Engine'})
    return jsonify({'delivered': delivered}), 200
