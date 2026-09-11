#!/usr/bin/env python3
"""
Admin-only blueprint: API key management (for the /api/v1/predict/*
external API) and the audit log viewer. Requires the 'admin' role claim.
"""
import hashlib
import logging
import secrets

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from psycopg2.extras import RealDictCursor

from rbac import role_required
from audit import get_db_connection, record_audit
from cache import cache_get, cache_set

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def init_admin_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                key_hash VARCHAR(255) UNIQUE NOT NULL,
                key_prefix VARCHAR(16) NOT NULL,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                last_used_at TIMESTAMP,
                revoked BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM api_keys")
        if cur.fetchone()[0] == 0:
            raw_key = 'cik_' + secrets.token_urlsafe(32)
            cur.execute(
                """INSERT INTO api_keys (name, key_hash, key_prefix, created_by)
                   VALUES (%s, %s, %s, %s)""",
                ('Default bootstrap key', _hash_key(raw_key), raw_key[:12], 'system')
            )
            conn.commit()
            logger.info(f"[Admin] Seeded default API key for /api/v1/predict/*: {raw_key}")
    finally:
        cur.close()
        conn.close()


def _hash_key(raw_key):
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def verify_api_key(raw_key):
    """Validate an X-API-Key header value against stored (hashed) keys."""
    if not raw_key:
        return False

    key_hash = _hash_key(raw_key)
    cached = cache_get(f'apikey_valid:{key_hash}')
    if cached is not None:
        return bool(cached)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM api_keys WHERE key_hash = %s AND revoked = FALSE", (key_hash,))
        row = cur.fetchone()
        valid = row is not None
        if valid:
            cur.execute("UPDATE api_keys SET last_used_at = NOW() WHERE id = %s", (row['id'],))
            conn.commit()
    finally:
        cur.close()
        conn.close()

    cache_set(f'apikey_valid:{key_hash}', valid, ttl=30)
    return valid


@admin_bp.route('/api-keys', methods=['POST'])
@role_required('admin')
def create_api_key():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or 'Unnamed key').strip()
    username = get_jwt_identity()

    raw_key = 'cik_' + secrets.token_urlsafe(32)
    key_hash = _hash_key(raw_key)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """INSERT INTO api_keys (name, key_hash, key_prefix, created_by)
               VALUES (%s, %s, %s, %s) RETURNING id, name, key_prefix, created_at""",
            (name, key_hash, raw_key[:12], username)
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'api_key_created', f"id={row['id']} name={name}")

    return jsonify({
        'api_key': raw_key,  # returned once; caller must store it securely
        'id': row['id'],
        'name': row['name'],
        'key_prefix': row['key_prefix'],
        'created_at': row['created_at'],
    }), 201


@admin_bp.route('/api-keys', methods=['GET'])
@role_required('admin')
def list_api_keys():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, name, key_prefix, created_by, created_at, last_used_at, revoked
            FROM api_keys ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return jsonify({'api_keys': rows}), 200


@admin_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@role_required('admin')
def revoke_api_key(key_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE api_keys SET revoked = TRUE WHERE id = %s", (key_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'api_key_revoked', f"id={key_id}")
    return jsonify({'message': 'API key revoked'}), 200


@admin_bp.route('/audit-log', methods=['GET'])
@role_required('admin')
def get_audit_log():
    page = max(int(request.args.get('page', 1) or 1), 1)
    page_size = min(max(int(request.args.get('page_size', 25) or 25), 1), 100)
    offset = (page - 1) * page_size

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT COUNT(*) as total FROM audit_log")
        total = cur.fetchone()['total']

        cur.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (page_size, offset)
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return jsonify({
        'results': rows,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size if page_size else 0,
    }), 200
