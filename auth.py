#!/usr/bin/env python3
"""
JWT-based authentication blueprint.
Handles registration, login, token refresh, current-user lookup and
logout (via a Redis-backed token blocklist since JWTs are stateless).
"""
import os
import time
import logging
from datetime import timedelta

import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)

from cache import get_redis
from extensions import limiter
from audit import record_audit
from twofa import is_2fa_enabled

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_auth_db():
    """Create the users table and seed a default admin account if empty."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'analyst',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            default_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ('admin', 'admin@intelligence.local', default_hash, 'admin')
            )
            conn.commit()
            logger.info("[Auth] Seeded default admin user (admin / admin123)")
    finally:
        cur.close()
        conn.close()


def _serialize_user(row):
    return {
        'id': row['id'],
        'username': row['username'],
        'email': row['email'],
        'role': row['role'],
    }


@auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per minute')
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not username or not email or len(password) < 6:
        return jsonify({'error': 'username, email and password (min 6 chars) are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            return jsonify({'error': 'Username or email already registered'}), 409

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            """INSERT INTO users (username, email, password_hash, role)
               VALUES (%s, %s, %s, 'analyst') RETURNING id, username, email, role""",
            (username, email, password_hash)
        )
        user = cur.fetchone()
        conn.commit()

        access_token = create_access_token(identity=user['username'], additional_claims={'role': user['role']})
        refresh_token = create_refresh_token(identity=user['username'])

        record_audit(user['username'], 'user_registered', request.headers.get('User-Agent', ''), request.remote_addr)

        return jsonify({
            'user': _serialize_user(user),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }), 201
    except Exception as e:
        conn.rollback()
        logger.error(f"[Auth] register failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500
    finally:
        cur.close()
        conn.close()


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            record_audit(username, 'login_failed', request.remote_addr or '')
            return jsonify({'error': 'Invalid username or password'}), 401

        if is_2fa_enabled(user['username']):
            pre_auth_token = create_access_token(
                identity=user['username'],
                additional_claims={'pre_auth': True},
                expires_delta=timedelta(minutes=5)
            )
            record_audit(user['username'], 'login_password_ok_awaiting_2fa', request.remote_addr or '')
            return jsonify({'requires_2fa': True, 'temp_token': pre_auth_token}), 200

        access_token = create_access_token(identity=user['username'], additional_claims={'role': user['role']})
        refresh_token = create_refresh_token(identity=user['username'])

        record_audit(user['username'], 'login_success', request.headers.get('User-Agent', ''), request.remote_addr)

        return jsonify({
            'user': _serialize_user(user),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }), 200
    finally:
        cur.close()
        conn.close()


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    identity = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, username, email, role FROM users WHERE username = %s", (identity,))
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(_serialize_user(user)), 200
    finally:
        cur.close()
        conn.close()


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    token = get_jwt()
    ttl = max(int(token['exp'] - time.time()), 1)
    get_redis().setex(f"revoked_token:{token['jti']}", ttl, '1')
    record_audit(get_jwt_identity(), 'logout', request.remote_addr or '')
    return jsonify({'message': 'Logged out successfully'}), 200
