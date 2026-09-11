#!/usr/bin/env python3
"""
Lightweight audit trail for security-relevant actions (auth events,
exports, API key changes) persisted to Postgres.
"""
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_audit_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                action VARCHAR(100) NOT NULL,
                detail TEXT,
                ip_address VARCHAR(64),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def record_audit(username, action, detail='', ip_address=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_log (username, action, detail, ip_address) VALUES (%s, %s, %s, %s)",
            (username, action, detail, ip_address)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"[Audit] Failed to record '{action}' for {username}: {e}")
