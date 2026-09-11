#!/usr/bin/env python3
"""
Automated Insights: compares the current analytics snapshot against
the previous one (cached in Redis) and produces plain-English insight
strings surfaced on the dashboard, without requiring any external
LLM/API dependency.
"""
import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor

from cache import cache_get, cache_set
from audit import get_db_connection
from datasets_bp import get_active_dataset_id

logger = logging.getLogger(__name__)
insights_bp = Blueprint('insights', __name__, url_prefix='/analytics')


def _get_current_snapshot(dataset_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT risk_level, COUNT(*) as count FROM feature_churn_risk WHERE dataset_id = %s GROUP BY risk_level", (dataset_id,))
        risk = {row['risk_level']: row['count'] for row in cur.fetchall()}

        cur.execute("SELECT ROUND(AVG(engagement_score), 2) as avg_engagement FROM feature_engagement WHERE dataset_id = %s", (dataset_id,))
        engagement = cur.fetchone()['avg_engagement']

        cur.execute("""
            SELECT ROUND(AVG(lifetime_value), 2) as avg_ltv, ROUND(AVG(predicted_ltv), 2) as avg_predicted_ltv
            FROM feature_rfm WHERE dataset_id = %s
        """, (dataset_id,))
        ltv_row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    return {
        'high_risk': risk.get('HIGH', 0),
        'medium_risk': risk.get('MEDIUM', 0),
        'low_risk': risk.get('LOW', 0),
        'avg_engagement': float(engagement) if engagement is not None else 0.0,
        'avg_ltv': float(ltv_row['avg_ltv']) if ltv_row['avg_ltv'] is not None else 0.0,
        'avg_predicted_ltv': float(ltv_row['avg_predicted_ltv']) if ltv_row['avg_predicted_ltv'] is not None else 0.0,
    }


def _revenue_at_risk_insights(dataset_id):
    """Aggregate: how much lifetime value sits in HIGH-risk customers."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT COALESCE(SUM(fr.lifetime_value), 0) as total_at_risk, COUNT(*) as cnt
            FROM feature_churn_risk fc
            JOIN feature_rfm fr ON fr.customer_id = fc.customer_id AND fr.dataset_id = fc.dataset_id
            WHERE fc.dataset_id = %s AND fc.risk_level = 'HIGH'
        """, (dataset_id,))
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if row and row['cnt'] > 0:
        return [{
            'type': 'warning',
            'text': f"${float(row['total_at_risk']):,.2f} in lifetime value is concentrated in {row['cnt']:,} HIGH-risk customers.",
            'category': 'revenue',
        }]
    return []


def _segment_insights(dataset_id):
    """One insight per customer segment (VIP/STANDARD/AT_RISK/DORMANT) with real counts."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT segment, COUNT(*) as cnt, ROUND(AVG(engagement_score), 2) as avg_eng
            FROM feature_engagement WHERE dataset_id = %s GROUP BY segment
        """, (dataset_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    total = sum(r['cnt'] for r in rows) or 1
    insights = []
    for r in rows:
        pct = round(r['cnt'] / total * 100, 1)
        insights.append({
            'type': 'info',
            'text': f"{r['cnt']:,} customers ({pct}%) are in the {r['segment']} segment, averaging {r['avg_eng']} engagement.",
            'category': 'segment',
        })
    return insights


def _breakdown_insights(dataset_id, column, label):
    """Flags dimensions (country/channel/industry) with an elevated HIGH-risk concentration."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(f"""
            SELECT c.{column} as key, COUNT(*) as total,
                   COUNT(*) FILTER (WHERE fc.risk_level = 'HIGH') as high_risk
            FROM customers c
            JOIN feature_churn_risk fc ON fc.customer_id = c.customer_id AND fc.dataset_id = c.dataset_id
            WHERE c.dataset_id = %s AND c.{column} IS NOT NULL AND c.{column} != ''
            GROUP BY c.{column}
            HAVING COUNT(*) >= 5
            ORDER BY (COUNT(*) FILTER (WHERE fc.risk_level = 'HIGH'))::float / COUNT(*) DESC
            LIMIT 15
        """, (dataset_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    insights = []
    for r in rows:
        pct = round(r['high_risk'] / r['total'] * 100, 1) if r['total'] else 0
        if pct >= 15:
            insights.append({
                'type': 'warning',
                'text': f"{label} '{r['key']}' has an elevated churn rate: {r['high_risk']} of {r['total']} customers ({pct}%) are HIGH risk.",
                'category': column,
            })
    return insights


def _customer_risk_insights(dataset_id, limit=5000):
    """One granular insight per at-risk customer — this is what scales to hundreds/thousands per dataset."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT c.customer_id, c.first_name, c.last_name,
                   fc.risk_level, fc.churn_risk_score,
                   COALESCE(fr.lifetime_value, 0) as lifetime_value,
                   COALESCE(fe.engagement_score, 0) as engagement_score,
                   COALESCE(fs.total_tickets, 0) as total_tickets,
                   COALESCE(fs.satisfaction_score, 0) as satisfaction_score
            FROM feature_churn_risk fc
            JOIN customers c ON c.customer_id = fc.customer_id AND c.dataset_id = fc.dataset_id
            LEFT JOIN feature_rfm fr ON fr.customer_id = fc.customer_id AND fr.dataset_id = fc.dataset_id
            LEFT JOIN feature_engagement fe ON fe.customer_id = fc.customer_id AND fe.dataset_id = fc.dataset_id
            LEFT JOIN feature_support fs ON fs.customer_id = fc.customer_id AND fs.dataset_id = fc.dataset_id
            WHERE fc.dataset_id = %s AND fc.risk_level IN ('HIGH', 'MEDIUM')
            ORDER BY fr.lifetime_value DESC NULLS LAST
            LIMIT %s
        """, (dataset_id, limit))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    insights = []
    for r in rows:
        name = f"{r['first_name']} {r['last_name']}".strip() or r['customer_id']
        cid = r['customer_id']
        ltv = round(float(r['lifetime_value']), 2)
        risk = r['risk_level']
        score = round(float(r['churn_risk_score']), 2)

        if risk == 'HIGH' and ltv > 1000:
            text = f"{name} ({cid}) is a high-value customer (${ltv:,.2f} LTV) at HIGH churn risk — immediate retention outreach recommended."
            itype = 'warning'
        elif risk == 'HIGH' and r['total_tickets'] >= 3 and float(r['satisfaction_score']) < 3:
            text = f"{name} ({cid}) has {r['total_tickets']} support tickets with low satisfaction ({r['satisfaction_score']}/5) and is HIGH churn risk."
            itype = 'warning'
        elif risk == 'HIGH' and float(r['engagement_score']) < 20:
            text = f"{name} ({cid}) has very low engagement ({r['engagement_score']}) and is HIGH churn risk."
            itype = 'warning'
        elif risk == 'HIGH':
            text = f"{name} ({cid}) is flagged HIGH churn risk (score {score})."
            itype = 'warning'
        else:
            text = f"{name} ({cid}) shows early warning signs (MEDIUM churn risk, score {score})."
            itype = 'info'

        insights.append({'type': itype, 'text': text, 'category': 'customer_risk', 'customer_id': cid})

    return insights


def generate_insights_for_dataset(dataset_id):
    """Compare current metrics against the last snapshot and cache plain-English insights.

    Produces both a handful of trend-level insights and a large batch of granular,
    real-data-driven insights (per-customer risk callouts, segment/geo/channel/industry
    breakdowns, revenue-at-risk) so datasets with many customers surface hundreds to
    thousands of concrete, actionable insights rather than one generic summary line.
    """
    try:
        current = _get_current_snapshot(dataset_id)
        baseline = cache_get(f'insights:baseline:{dataset_id}')
        insights = []

        if baseline:
            high_delta = current['high_risk'] - baseline['high_risk']
            if high_delta > 0:
                insights.append({'type': 'warning', 'text': f"High churn-risk customers increased by {high_delta} since the last check.", 'category': 'trend'})
            elif high_delta < 0:
                insights.append({'type': 'positive', 'text': f"High churn-risk customers decreased by {abs(high_delta)} — good progress.", 'category': 'trend'})

            eng_delta = round(current['avg_engagement'] - baseline['avg_engagement'], 2)
            if abs(eng_delta) >= 0.5:
                direction = 'up' if eng_delta > 0 else 'down'
                insights.append({'type': 'info', 'text': f"Average engagement score is {direction} {abs(eng_delta)} points.", 'category': 'trend'})

        ltv_gap = round(current['avg_predicted_ltv'] - current['avg_ltv'], 2)
        if ltv_gap > 50:
            insights.append({'type': 'opportunity', 'text': f"Predicted LTV exceeds actual LTV by ${ltv_gap} on average — potential upsell opportunity.", 'category': 'trend'})

        if current['high_risk'] > current['low_risk']:
            insights.append({'type': 'warning', 'text': 'More customers are HIGH risk than LOW risk — consider a retention campaign.', 'category': 'trend'})

        insights.extend(_revenue_at_risk_insights(dataset_id))
        insights.extend(_segment_insights(dataset_id))
        insights.extend(_breakdown_insights(dataset_id, 'country', 'Country'))
        insights.extend(_breakdown_insights(dataset_id, 'acquisition_channel', 'Acquisition channel'))
        insights.extend(_breakdown_insights(dataset_id, 'industry', 'Industry'))
        insights.extend(_customer_risk_insights(dataset_id))

        if not insights:
            insights.append({'type': 'info', 'text': 'No significant changes detected since the last check.', 'category': 'trend'})

        cache_set(f'insights:baseline:{dataset_id}', current, ttl=86400)
        cache_set(f'insights:latest:{dataset_id}', {
            'insights': insights,
            'total_count': len(insights),
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }, ttl=86400)
        logger.info(f"[Insights] Generated {len(insights)} insight(s) for dataset {dataset_id}")
    except Exception as e:
        logger.error(f"[Insights] generation failed for dataset {dataset_id}: {e}")


def generate_insights():
    """Refresh cached insights for every dataset currently marked ready."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM datasets WHERE status = 'ready'")
        dataset_ids = [row['id'] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

    for dataset_id in dataset_ids:
        generate_insights_for_dataset(dataset_id)


@insights_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    data = cache_get(f'insights:latest:{dataset_id}')
    if not data:
        generate_insights_for_dataset(dataset_id)
        data = cache_get(f'insights:latest:{dataset_id}')
    return jsonify(data or {'insights': [], 'generated_at': None}), 200

