#!/usr/bin/env python3
"""
Cohort & retention analysis: groups customers by signup month and measures
month-over-month activity retention using real event data — no synthetic
or hardcoded numbers, purely derived from each dataset's own events table.
"""
import logging

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor

from audit import get_db_connection
from datasets_bp import get_active_dataset_id

logger = logging.getLogger(__name__)
cohort_bp = Blueprint('cohort', __name__, url_prefix='/analytics')

MAX_MONTH_OFFSET = 12


@cohort_bp.route('/cohort-retention', methods=['GET'])
@jwt_required()
def get_cohort_retention():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            WITH cohorts AS (
                SELECT customer_id, date_trunc('month', signup_date) AS cohort_month
                FROM customers WHERE dataset_id = %s AND signup_date IS NOT NULL
            ),
            cohort_sizes AS (
                SELECT cohort_month, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_month
            ),
            activity AS (
                SELECT DISTINCT e.customer_id, date_trunc('month', e.event_timestamp) AS activity_month
                FROM events e WHERE e.dataset_id = %s AND e.event_timestamp IS NOT NULL
            ),
            cohort_activity AS (
                SELECT
                    c.cohort_month,
                    (
                        (EXTRACT(YEAR FROM a.activity_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12 +
                        (EXTRACT(MONTH FROM a.activity_month) - EXTRACT(MONTH FROM c.cohort_month))
                    )::int AS month_offset,
                    COUNT(DISTINCT a.customer_id) AS active_customers
                FROM cohorts c
                JOIN activity a ON a.customer_id = c.customer_id
                GROUP BY c.cohort_month, month_offset
            )
            SELECT cs.cohort_month, cs.cohort_size, ca.month_offset, ca.active_customers
            FROM cohort_sizes cs
            LEFT JOIN cohort_activity ca ON ca.cohort_month = cs.cohort_month
                AND ca.month_offset BETWEEN 0 AND %s
            ORDER BY cs.cohort_month, ca.month_offset
        """, (dataset_id, dataset_id, MAX_MONTH_OFFSET))
        rows = cur.fetchall()
    except Exception as e:
        logger.error(f"[Cohort] retention query failed: {e}")
        return jsonify({'error': 'Failed to compute cohort retention'}), 500
    finally:
        cur.close()
        conn.close()

    cohorts = {}
    max_offset_seen = 0

    for r in rows:
        month_key = r['cohort_month'].strftime('%Y-%m') if r['cohort_month'] else 'unknown'

        if month_key not in cohorts:
            cohorts[month_key] = {
                'cohort_month': month_key,
                'cohort_size': r['cohort_size'],
                'retention': {},
            }

        if r['month_offset'] is not None and 0 <= r['month_offset'] <= MAX_MONTH_OFFSET:
            size = cohorts[month_key]['cohort_size'] or 0
            pct = round((r['active_customers'] or 0) / size * 100, 1) if size else 0.0
            cohorts[month_key]['retention'][r['month_offset']] = pct
            if r['month_offset'] > max_offset_seen:
                max_offset_seen = r['month_offset']

    result = []
    for cohort in sorted(cohorts.values(), key=lambda c: c['cohort_month']):
        retention = [None] * (max_offset_seen + 1)
        for offset, pct in cohort['retention'].items():
            retention[offset] = pct

        result.append({
            'cohort_month': cohort['cohort_month'],
            'cohort_size': cohort['cohort_size'],
            'retention': retention,
        })

    return jsonify({'cohorts': result, 'max_month_offset': max_offset_seen}), 200
