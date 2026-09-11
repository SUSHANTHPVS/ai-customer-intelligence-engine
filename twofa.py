#!/usr/bin/env python3
"""
TOTP-based Two-Factor Authentication (RFC 6238), compatible with
Google Authenticator / Authy. Adds an optional second login step on
top of the existing username/password + JWT flow.
"""
import base64
import io
import logging

import pyotp
import qrcode
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token
)
from psycopg2.extras import RealDictCursor

from audit import get_db_connection, record_audit

logger = logging.getLogger(__name__)
twofa_bp = Blueprint('twofa', __name__, url_prefix='/auth/2fa')

ISSUER_NAME = 'Customer Intelligence Engine'


def init_2fa_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64)")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def is_2fa_enabled(username):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT totp_enabled FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        return bool(row and row['totp_enabled'])
    finally:
        cur.close()
        conn.close()


def verify_totp(username, code):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT totp_secret FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row or not row['totp_secret']:
            return False
        return pyotp.TOTP(row['totp_secret']).verify(code, valid_window=1)
    finally:
        cur.close()
        conn.close()


@twofa_bp.route('/setup', methods=['POST'])
@jwt_required()
def setup_2fa():
    """Generate (or reuse a pending) TOTP secret + QR code, not yet enabled until verified.

    Idempotent while enrollment is in progress so re-opening the setup dialog
    doesn't invalidate a secret the user already scanned into their app.
    """
    username = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT totp_secret, totp_enabled FROM users WHERE username = %s", (username,))
        row = cur.fetchone()

        if row and row['totp_secret'] and not row['totp_enabled']:
            secret = row['totp_secret']
        else:
            secret = pyotp.random_base32()
            cur.execute(
                "UPDATE users SET totp_secret = %s, totp_enabled = FALSE WHERE username = %s",
                (secret, username)
            )
            conn.commit()
    finally:
        cur.close()
        conn.close()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=ISSUER_NAME)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return jsonify({'secret': secret, 'qr_code': f'data:image/png;base64,{qr_base64}'}), 200


@twofa_bp.route('/enable', methods=['POST'])
@jwt_required()
def enable_2fa():
    username = get_jwt_identity()
    code = (request.get_json(silent=True) or {}).get('code', '')

    if not verify_totp(username, code):
        return jsonify({'error': 'Invalid verification code'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET totp_enabled = TRUE WHERE username = %s", (username,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, '2fa_enabled')
    return jsonify({'message': '2FA enabled successfully'}), 200


@twofa_bp.route('/disable', methods=['POST'])
@jwt_required()
def disable_2fa():
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET totp_enabled = FALSE, totp_secret = NULL WHERE username = %s", (username,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, '2fa_disabled')
    return jsonify({'message': '2FA disabled'}), 200


@twofa_bp.route('/status', methods=['GET'])
@jwt_required()
def status_2fa():
    return jsonify({'enabled': is_2fa_enabled(get_jwt_identity())}), 200


@twofa_bp.route('/login-verify', methods=['POST'])
@jwt_required()
def login_verify():
    """Complete login using the short-lived pre-auth token issued by /auth/login."""
    claims = get_jwt()
    if not claims.get('pre_auth'):
        return jsonify({'error': 'Invalid or expired 2FA session'}), 400

    username = get_jwt_identity()
    code = (request.get_json(silent=True) or {}).get('code', '')

    if not verify_totp(username, code):
        record_audit(username, 'login_2fa_failed')
        return jsonify({'error': 'Invalid 2FA code'}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, username, email, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    access_token = create_access_token(identity=user['username'], additional_claims={'role': user['role']})
    refresh_token = create_refresh_token(identity=user['username'])
    record_audit(username, 'login_success_2fa')

    return jsonify({
        'user': dict(user),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200
