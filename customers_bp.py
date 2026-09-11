#!/usr/bin/env python3
"""
Customer 360 search & profile blueprint.
Provides paginated/filterable customer search and a full profile view
that joins every feature table for a single customer.
"""
import logging
import os

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from datasets_bp import get_active_dataset_id

logger = logging.getLogger(__name__)
customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def _generate_recommendations(profile):
    """Rule-based next-best-action suggestions derived from the customer's own feature data."""
    recs = []
    churn_risk = profile.get('churn_risk') or {}
    rfm = profile.get('rfm') or {}
    engagement = profile.get('engagement') or {}
    revenue = profile.get('revenue') or {}
    support = profile.get('support') or {}

    risk_level = churn_risk.get('risk_level')
    recency = rfm.get('recency') or 0
    frequency = rfm.get('frequency') or 0
    engagement_score = float(engagement.get('engagement_score') or 0)
    segment = engagement.get('segment')
    total_tickets = support.get('total_tickets') or 0
    satisfaction = float(support.get('satisfaction_score') or 0)
    total_revenue = float(revenue.get('total_revenue') or 0)

    if risk_level == 'HIGH' and recency > 60:
        recs.append({
            'priority': 'high',
            'text': f"No activity in {recency} days — send a personalized win-back email or offer.",
        })
    if risk_level == 'HIGH' and total_tickets >= 3 and satisfaction < 3:
        recs.append({
            'priority': 'high',
            'text': f"{total_tickets} support tickets with low satisfaction ({satisfaction}/5) — escalate to a senior support rep.",
        })
    if engagement_score < 20:
        recs.append({
            'priority': 'medium',
            'text': 'Low product engagement — trigger an onboarding or feature-adoption campaign.',
        })
    if segment == 'VIP' and risk_level in ('HIGH', 'MEDIUM'):
        recs.append({
            'priority': 'high',
            'text': 'High-value VIP at risk — assign a dedicated customer success manager for proactive outreach.',
        })
    if total_revenue > 500 and frequency <= 2:
        recs.append({
            'priority': 'medium',
            'text': 'High spend but infrequent purchases — offer a loyalty program or subscription upgrade.',
        })
    if not recs:
        if risk_level == 'LOW':
            recs.append({'priority': 'low', 'text': 'Customer is healthy — no immediate action needed.'})
        else:
            recs.append({'priority': 'low', 'text': 'Monitor for changes — no urgent risk signals detected yet.'})

    return recs


@customers_bp.route('/search', methods=['GET'])
@jwt_required()
def search_customers():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    q = request.args.get('q', '').strip()
    segment = request.args.get('segment', '').strip().upper()
    risk_level = request.args.get('risk_level', '').strip().upper()
    page = max(int(request.args.get('page', 1) or 1), 1)
    page_size = min(max(int(request.args.get('page_size', 20) or 20), 1), 100)
    offset = (page - 1) * page_size

    conditions = ["c.dataset_id = %s"]
    params = [dataset_id]

    if q:
        like = f"%{q}%"
        conditions.append(
            "(c.customer_id ILIKE %s OR c.first_name ILIKE %s OR c.last_name ILIKE %s OR c.email ILIKE %s)"
        )
        params.extend([like, like, like, like])
    if segment:
        conditions.append("fe.segment = %s")
        params.append(segment)
    if risk_level:
        conditions.append("fc.risk_level = %s")
        params.append(risk_level)

    where_clause = f"WHERE {' AND '.join(conditions)}"

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(f"""
            SELECT COUNT(*) as total
            FROM customers c
            LEFT JOIN feature_engagement fe ON c.customer_id = fe.customer_id
            LEFT JOIN feature_churn_risk fc ON c.customer_id = fc.customer_id
            {where_clause}
        """, params)
        total = cur.fetchone()['total']

        cur.execute(f"""
            SELECT
                c.customer_id, c.first_name, c.last_name, c.email, c.country,
                c.industry, c.acquisition_channel, c.signup_date,
                fe.segment, fe.engagement_score,
                fc.risk_level, fc.churn_risk_score,
                fr.lifetime_value
            FROM customers c
            LEFT JOIN feature_engagement fe ON c.customer_id = fe.customer_id
            LEFT JOIN feature_churn_risk fc ON c.customer_id = fc.customer_id
            LEFT JOIN feature_rfm fr ON c.customer_id = fr.customer_id
            {where_clause}
            ORDER BY c.customer_id
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])
        rows = cur.fetchall()

        return jsonify({
            'results': rows,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size else 0,
        }), 200
    except Exception as e:
        logger.error(f"[Customers] search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500
    finally:
        cur.close()
        conn.close()


@customers_bp.route('/<customer_id>/profile', methods=['GET'])
@jwt_required()
def customer_profile(customer_id):
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM customers WHERE customer_id = %s AND dataset_id = %s",
            (customer_id, dataset_id)
        )
        customer = cur.fetchone()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        feature_tables = {
            'rfm': 'feature_rfm',
            'behavioral': 'feature_behavioral',
            'engagement': 'feature_engagement',
            'revenue': 'feature_revenue',
            'support': 'feature_support',
            'churn_risk': 'feature_churn_risk',
        }
        profile = {'customer': customer}
        for key, table in feature_tables.items():
            cur.execute(
                f"SELECT * FROM {table} WHERE customer_id = %s AND dataset_id = %s",
                (customer_id, dataset_id)
            )
            profile[key] = cur.fetchone()

        profile['recommendations'] = _generate_recommendations(profile)

        return jsonify(profile), 200
    except Exception as e:
        logger.error(f"[Customers] profile fetch failed: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500
    finally:
        cur.close()
        conn.close()
