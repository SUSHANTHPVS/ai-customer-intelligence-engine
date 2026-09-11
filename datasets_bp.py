#!/usr/bin/env python3
"""
Multi-tenant dataset management.

Any authenticated user can upload their own CSV files (customers,
events, transactions, support_tickets) and get a fully isolated,
feature-engineered analytics dataset scoped to their account. Existing
rows (customer_id/event_id/etc.) are namespaced per dataset so different
uploads can freely reuse the same raw IDs without colliding.
"""
import csv
import io
import logging
import secrets
import threading
from datetime import date, datetime

from psycopg2.extras import RealDictCursor, execute_batch, Json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from audit import get_db_connection, record_audit

logger = logging.getLogger(__name__)
datasets_bp = Blueprint('datasets', __name__, url_prefix='/datasets')

FEATURE_TABLES = [
    'feature_rfm', 'feature_behavioral', 'feature_engagement',
    'feature_revenue', 'feature_support', 'feature_churn_risk'
]
RAW_TABLES = ['customers', 'events', 'transactions', 'support_tickets']

CUSTOMERS_REQUIRED = {
    'customer_id', 'first_name', 'last_name', 'email',
    'country', 'industry', 'acquisition_channel', 'signup_date'
}

MAX_CUSTOMERS_ROWS = 20000
MAX_EVENTS_ROWS = 1_000_000_000_000_000_000_000  # effectively unbounded; MAX_CONTENT_LENGTH is the real upload gate
ID_SEPARATOR = '::'


def init_datasets_db():
    """Create the datasets table and add dataset_id scoping columns to every data table."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                owner_username VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'processing',
                row_counts JSONB,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS active_dataset_id VARCHAR(64)")
        cur.execute("ALTER TABLE datasets ADD COLUMN IF NOT EXISTS quality_report JSONB")
        cur.execute("ALTER TABLE datasets ADD COLUMN IF NOT EXISTS model_metrics JSONB")
        cur.execute("ALTER TABLE datasets ADD COLUMN IF NOT EXISTS anomaly_report JSONB")

        for table in RAW_TABLES + FEATURE_TABLES:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS dataset_id VARCHAR(64) NOT NULL DEFAULT 'default'")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_dataset_id ON {table}(dataset_id)")

        cur.execute("SELECT 1 FROM datasets WHERE id = 'default'")
        if not cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM customers WHERE dataset_id = 'default'")
            customer_count = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO datasets (id, name, owner_username, status, row_counts)
                   VALUES ('default', %s, 'system', 'ready', %s)""",
                (f'Demo Dataset ({customer_count:,} customers)', Json({'customers': customer_count}))
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_active_dataset_id(username):
    if not username:
        return 'default'
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT active_dataset_id FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        return (row and row['active_dataset_id']) or 'default'
    finally:
        cur.close()
        conn.close()


def _prefixed(dataset_id, raw_id):
    return f"{dataset_id}{ID_SEPARATOR}{raw_id}"


def _to_float(value, default=0.0):
    try:
        return float(value) if value not in (None, '') else default
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(float(value)) if value not in (None, '') else default
    except (TypeError, ValueError):
        return default


def _read_csv_rows(file_storage):
    text = file_storage.read().decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(text)))


@datasets_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_dataset():
    username = get_jwt_identity()

    if 'customers' not in request.files or not request.files['customers'].filename:
        return jsonify({'error': 'customers.csv is required (form field "customers")'}), 400

    try:
        customers_rows = _read_csv_rows(request.files['customers'])
    except UnicodeDecodeError:
        return jsonify({'error': 'customers.csv must be UTF-8 encoded'}), 400

    if not customers_rows:
        return jsonify({'error': 'customers.csv is empty'}), 400
    if not CUSTOMERS_REQUIRED.issubset(set(customers_rows[0].keys())):
        missing = CUSTOMERS_REQUIRED - set(customers_rows[0].keys())
        return jsonify({'error': f"customers.csv missing columns: {', '.join(sorted(missing))}"}), 400
    if len(customers_rows) > MAX_CUSTOMERS_ROWS:
        return jsonify({'error': f'customers.csv exceeds the {MAX_CUSTOMERS_ROWS:,} row limit'}), 400

    events_rows, transactions_rows, support_rows = [], [], []
    try:
        if request.files.get('events') and request.files['events'].filename:
            events_rows = _read_csv_rows(request.files['events'])
            if len(events_rows) > MAX_EVENTS_ROWS:
                return jsonify({'error': f'events.csv exceeds the {MAX_EVENTS_ROWS:,} row limit'}), 400
        if request.files.get('transactions') and request.files['transactions'].filename:
            transactions_rows = _read_csv_rows(request.files['transactions'])
        if request.files.get('support_tickets') and request.files['support_tickets'].filename:
            support_rows = _read_csv_rows(request.files['support_tickets'])
    except UnicodeDecodeError:
        return jsonify({'error': 'All files must be UTF-8 encoded'}), 400

    dataset_id = 'ds_' + secrets.token_hex(6)
    name = (request.form.get('name') or f"Dataset {datetime.now().strftime('%Y-%m-%d %H:%M')}").strip()[:200]

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO datasets (id, name, owner_username, status) VALUES (%s, %s, %s, 'processing')",
            (dataset_id, name, username)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    thread = threading.Thread(
        target=_process_dataset,
        args=(dataset_id, username, customers_rows, events_rows, transactions_rows, support_rows),
        daemon=True
    )
    thread.start()

    record_audit(username, 'dataset_upload_started', f"id={dataset_id} customers={len(customers_rows)}")

    return jsonify({'dataset_id': dataset_id, 'name': name, 'status': 'processing'}), 202


def _compute_quality_report(customers_rows):
    """Basic data-quality checks over the raw customers CSV rows before dedup/insert."""
    total = len(customers_rows)
    seen_ids = set()
    duplicate_ids = 0
    missing_email = 0
    missing_name = 0
    for row in customers_rows:
        cid = row.get('customer_id', '')
        if cid in seen_ids:
            duplicate_ids += 1
        else:
            seen_ids.add(cid)
        if not (row.get('email') or '').strip():
            missing_email += 1
        if not (row.get('first_name') or '').strip() or not (row.get('last_name') or '').strip():
            missing_name += 1

    issues = duplicate_ids + missing_email + missing_name
    completeness_pct = round(max(0.0, 100.0 - (issues / max(total, 1)) * 100.0), 1)
    return {
        'total_rows': total,
        'duplicate_customer_ids': duplicate_ids,
        'missing_email': missing_email,
        'missing_name': missing_name,
        'completeness_pct': completeness_pct,
    }


def _process_dataset(dataset_id, username, customers_rows, events_rows, transactions_rows, support_rows):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        quality_report = _compute_quality_report(customers_rows)

        customer_records = [
            (
                _prefixed(dataset_id, row['customer_id']), row.get('first_name', ''), row.get('last_name', ''),
                row.get('email', ''), row.get('country', ''), row.get('industry', ''),
                row.get('acquisition_channel', ''), row.get('signup_date') or None, dataset_id
            )
            for row in customers_rows
        ]
        execute_batch(cur, """
            INSERT INTO customers (customer_id, first_name, last_name, email, country, industry,
                                    acquisition_channel, signup_date, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING
        """, customer_records, page_size=500)

        if events_rows:
            event_records = [
                (
                    _prefixed(dataset_id, row['event_id']), _prefixed(dataset_id, row['customer_id']),
                    row.get('event_type', ''), row.get('feature', ''), row.get('event_timestamp') or None,
                    _to_int(row.get('session_duration_seconds')), _to_float(row.get('event_value')),
                    dataset_id
                )
                for row in events_rows
            ]
            execute_batch(cur, """
                INSERT INTO events (event_id, customer_id, event_type, feature, event_timestamp,
                                     session_duration_seconds, event_value, dataset_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """, event_records, page_size=1000)

        if transactions_rows:
            txn_records = [
                (
                    _prefixed(dataset_id, row['transaction_id']), _prefixed(dataset_id, row['customer_id']),
                    row.get('transaction_type', ''), row.get('subscription_plan', ''),
                    _to_float(row.get('amount')), row.get('currency', 'USD'),
                    row.get('payment_method', ''), row.get('payment_status', ''),
                    row.get('transaction_timestamp') or None, dataset_id
                )
                for row in transactions_rows
            ]
            execute_batch(cur, """
                INSERT INTO transactions (transaction_id, customer_id, transaction_type, subscription_plan,
                                           amount, currency, payment_method, payment_status,
                                           transaction_timestamp, dataset_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (transaction_id) DO NOTHING
            """, txn_records, page_size=500)

        if support_rows:
            ticket_records = [
                (
                    _prefixed(dataset_id, row['ticket_id']), _prefixed(dataset_id, row['customer_id']),
                    row.get('category', ''), row.get('priority', ''),
                    _to_float(row.get('resolution_time_hours')), _to_int(row.get('satisfaction_score')),
                    row.get('created_at') or None, dataset_id
                )
                for row in support_rows
            ]
            execute_batch(cur, """
                INSERT INTO support_tickets (ticket_id, customer_id, category, priority,
                                              resolution_time_hours, satisfaction_score, created_at, dataset_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticket_id) DO NOTHING
            """, ticket_records, page_size=500)

        conn.commit()

        _compute_features(conn, dataset_id)

        row_counts = {
            'customers': len(customer_records),
            'events': len(events_rows),
            'transactions': len(transactions_rows),
            'support_tickets': len(support_rows),
        }
        cur.execute(
            "UPDATE datasets SET status = 'ready', row_counts = %s, quality_report = %s WHERE id = %s",
            (Json(row_counts), Json(quality_report), dataset_id)
        )
        cur.execute("UPDATE users SET active_dataset_id = %s WHERE username = %s", (dataset_id, username))
        conn.commit()
        cur.close()

        logger.info(f"[Datasets] Dataset {dataset_id} ready: {row_counts}")
    except Exception as e:
        logger.error(f"[Datasets] Processing failed for {dataset_id}: {e}")
        if conn:
            try:
                conn.rollback()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE datasets SET status = 'failed', error_message = %s WHERE id = %s",
                    (str(e)[:500], dataset_id)
                )
                conn.commit()
                cur.close()
            except Exception as inner:
                logger.error(f"[Datasets] Failed to record failure status: {inner}")
    finally:
        if conn:
            conn.close()


def _compute_features(conn, dataset_id):
    """Aggregate raw tables into the 6 feature tables, scoped to this dataset only."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT customer_id FROM customers WHERE dataset_id = %s ORDER BY customer_id", (dataset_id,))
    customer_ids = [r['customer_id'] for r in cur.fetchall()]
    today = date.today()

    for cid in customer_ids:
        cur.execute("""
            SELECT COALESCE(MAX(transaction_timestamp)::date, CURRENT_DATE) as recency_date,
                   COUNT(DISTINCT transaction_id) as frequency,
                   COALESCE(SUM(amount), 0)::numeric(12,2) as monetary
            FROM transactions WHERE customer_id = %s AND dataset_id = %s
        """, (cid, dataset_id))
        rfm = cur.fetchone()
        recency = (today - rfm['recency_date']).days if rfm['recency_date'] else 999
        frequency = _to_int(rfm['frequency'])
        monetary = _to_float(rfm['monetary'])
        predicted_ltv = monetary * (1 + frequency * 0.1) if frequency > 0 else 0
        if frequency > 20 and recency < 30 and monetary > 1000:
            rfm_segment = 'VIP'
        elif frequency > 10 and recency < 60 and monetary > 500:
            rfm_segment = 'Active'
        elif recency > 120:
            rfm_segment = 'Dormant'
        else:
            rfm_segment = 'Regular'

        cur.execute("""
            SELECT COALESCE(AVG(session_duration_seconds), 0)::integer as avg_session,
                   COUNT(DISTINCT event_timestamp::date) as login_freq,
                   COUNT(DISTINCT CASE WHEN event_type = 'feature_adoption' THEN event_type END) as feature_count,
                   COALESCE(MAX(event_timestamp::date), CURRENT_DATE) as last_active
            FROM events WHERE customer_id = %s AND dataset_id = %s
        """, (cid, dataset_id))
        behav = cur.fetchone()
        avg_session_duration = _to_int(behav['avg_session'])
        login_freq = _to_int(behav['login_freq'])
        feature_count = _to_int(behav['feature_count'])
        days_since_signup = (today - behav['last_active']).days if behav['last_active'] else 999

        cur.execute("""
            SELECT COUNT(DISTINCT CASE WHEN event_timestamp > NOW() - INTERVAL '30 days' THEN event_id END) as active_30,
                   COUNT(DISTINCT event_type) as feature_usage,
                   COUNT(*) as total_events
            FROM events WHERE customer_id = %s AND dataset_id = %s
        """, (cid, dataset_id))
        eng = cur.fetchone()
        active_30 = _to_int(eng['active_30'])
        feature_usage = _to_int(eng['feature_usage'])
        total_events = _to_int(eng['total_events'])
        engagement_score = min(100.0, (active_30 * 2) + (feature_usage * 3) + max(0, login_freq / 10.0))

        if engagement_score >= 70 and monetary >= 500:
            segment = 'VIP'
        elif engagement_score < 30 or recency > 90:
            segment = 'AT_RISK'
        elif total_events == 0:
            segment = 'DORMANT'
        else:
            segment = 'STANDARD'
        engagement_trend = 'upward' if active_30 > login_freq / 10 else ('stable' if active_30 == login_freq / 10 else 'downward')

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)::numeric(12,2) as total_revenue,
                   COUNT(*) as order_count,
                   COALESCE(MAX(subscription_plan), 'basic') as subscription,
                   COALESCE(AVG(amount), 0)::numeric(10,2) as avg_order_val
            FROM transactions WHERE customer_id = %s AND dataset_id = %s
        """, (cid, dataset_id))
        rev = cur.fetchone()
        total_rev = _to_float(rev['total_revenue'])
        order_count = _to_int(rev['order_count'])
        avg_order_val = _to_float(rev['avg_order_val'])
        mrr = round(total_rev / 12.0, 2) if order_count > 0 else 0
        arr = total_rev if order_count > 0 else 0

        cur.execute("""
            SELECT COUNT(*) as total_tickets,
                   COALESCE(AVG(resolution_time_hours), 0)::numeric(8,2) as avg_resolution,
                   COALESCE(AVG(satisfaction_score), 0)::numeric(3,2) as satisfaction
            FROM support_tickets WHERE customer_id = %s AND dataset_id = %s
        """, (cid, dataset_id))
        supp = cur.fetchone()
        total_tickets = _to_int(supp['total_tickets'])
        avg_resolution = _to_float(supp['avg_resolution'])
        satisfaction = _to_float(supp['satisfaction'])
        support_tier = 'premium' if total_tickets > 5 else 'standard'

        if recency > 60:
            churn_risk_score = 0.90
        elif recency > 30:
            churn_risk_score = 0.60
        elif engagement_score < 30:
            churn_risk_score = 0.70
        else:
            churn_risk_score = max(0.0, 0.50 - (engagement_score / 200.0))
        risk_level = 'HIGH' if churn_risk_score >= 0.7 else ('MEDIUM' if churn_risk_score >= 0.4 else 'LOW')

        cur.execute("""
            INSERT INTO feature_rfm (customer_id, recency, frequency, monetary, rfm_segment,
                                      lifetime_value, predicted_ltv, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                recency = EXCLUDED.recency, frequency = EXCLUDED.frequency, monetary = EXCLUDED.monetary,
                rfm_segment = EXCLUDED.rfm_segment, lifetime_value = EXCLUDED.lifetime_value,
                predicted_ltv = EXCLUDED.predicted_ltv
        """, (cid, recency, frequency, monetary, rfm_segment, monetary, predicted_ltv, dataset_id))

        cur.execute("""
            INSERT INTO feature_behavioral (customer_id, avg_session_duration, login_frequency,
                                             feature_adoption_count, days_since_signup, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                avg_session_duration = EXCLUDED.avg_session_duration, login_frequency = EXCLUDED.login_frequency,
                feature_adoption_count = EXCLUDED.feature_adoption_count, days_since_signup = EXCLUDED.days_since_signup
        """, (cid, avg_session_duration, login_freq, feature_count, days_since_signup, dataset_id))

        cur.execute("""
            INSERT INTO feature_engagement (customer_id, engagement_score, segment, active_days_last_30,
                                             feature_usage_count, last_engagement, engagement_trend, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                engagement_score = EXCLUDED.engagement_score, segment = EXCLUDED.segment,
                active_days_last_30 = EXCLUDED.active_days_last_30, feature_usage_count = EXCLUDED.feature_usage_count,
                last_engagement = EXCLUDED.last_engagement, engagement_trend = EXCLUDED.engagement_trend
        """, (cid, engagement_score, segment, active_30, feature_usage, behav['last_active'], engagement_trend, dataset_id))

        cur.execute("""
            INSERT INTO feature_revenue (customer_id, total_revenue, avg_order_value, subscription_plan,
                                          mrr, arr, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue, avg_order_value = EXCLUDED.avg_order_value,
                subscription_plan = EXCLUDED.subscription_plan, mrr = EXCLUDED.mrr, arr = EXCLUDED.arr
        """, (cid, total_rev, avg_order_val, rev['subscription'], mrr, arr, dataset_id))

        cur.execute("""
            INSERT INTO feature_support (customer_id, total_tickets, avg_resolution_time,
                                          satisfaction_score, support_tier, dataset_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                total_tickets = EXCLUDED.total_tickets, avg_resolution_time = EXCLUDED.avg_resolution_time,
                satisfaction_score = EXCLUDED.satisfaction_score, support_tier = EXCLUDED.support_tier
        """, (cid, total_tickets, avg_resolution, satisfaction, support_tier, dataset_id))

        cur.execute("""
            INSERT INTO feature_churn_risk (customer_id, churn_risk_score, churn_risk_category,
                                             risk_level, dataset_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                churn_risk_score = EXCLUDED.churn_risk_score, churn_risk_category = EXCLUDED.churn_risk_category,
                risk_level = EXCLUDED.risk_level
        """, (cid, churn_risk_score, risk_level, risk_level, dataset_id))

    conn.commit()
    cur.close()


@datasets_bp.route('', methods=['GET'])
@jwt_required()
def list_datasets():
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, name, owner_username, status, row_counts, error_message, created_at,
                   quality_report, model_metrics, anomaly_report
            FROM datasets
            WHERE owner_username = %s OR id = 'default'
            ORDER BY (id = 'default'), created_at DESC
        """, (username,))
        rows = cur.fetchall()

        cur.execute("SELECT active_dataset_id FROM users WHERE username = %s", (username,))
        active = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    return jsonify({
        'datasets': rows,
        'active_dataset_id': (active and active['active_dataset_id']) or 'default',
    }), 200


@datasets_bp.route('/<dataset_id>/status', methods=['GET'])
@jwt_required()
def dataset_status(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, status, row_counts, error_message, quality_report, model_metrics, anomaly_report FROM datasets "
            "WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        return jsonify({'error': 'Dataset not found'}), 404
    return jsonify(row), 200


@datasets_bp.route('/<dataset_id>/activate', methods=['POST'])
@jwt_required()
def activate_dataset(dataset_id):
    username = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, status FROM datasets WHERE id = %s AND (owner_username = %s OR id = 'default')",
            (dataset_id, username)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Dataset not found'}), 404
        if row['status'] != 'ready':
            return jsonify({'error': f"Dataset is not ready (status: {row['status']})"}), 400

        cur.execute("UPDATE users SET active_dataset_id = %s WHERE username = %s", (dataset_id, username))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'dataset_activated', f"id={dataset_id}")
    return jsonify({'message': 'Dataset activated', 'dataset_id': dataset_id}), 200


@datasets_bp.route('/<dataset_id>', methods=['DELETE'])
@jwt_required()
def delete_dataset(dataset_id):
    username = get_jwt_identity()
    if dataset_id == 'default':
        return jsonify({'error': 'The default demo dataset cannot be deleted'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM datasets WHERE id = %s AND owner_username = %s", (dataset_id, username))
        if not cur.fetchone():
            return jsonify({'error': 'Dataset not found'}), 404

        for table in FEATURE_TABLES + ['events', 'transactions', 'support_tickets', 'customers']:
            cur.execute(f"DELETE FROM {table} WHERE dataset_id = %s", (dataset_id,))
        cur.execute("DELETE FROM datasets WHERE id = %s", (dataset_id,))
        cur.execute(
            "UPDATE users SET active_dataset_id = NULL WHERE username = %s AND active_dataset_id = %s",
            (username, dataset_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'dataset_deleted', f"id={dataset_id}")
    return jsonify({'message': 'Dataset deleted'}), 200


def _compute_quality_report_from_db(dataset_id):
    """Regenerate quality report by scanning the already-stored customers table."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT customer_id, email, first_name, last_name FROM customers WHERE dataset_id = %s",
            (dataset_id,)
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    total = len(rows)
    if total == 0:
        return {
            'total_rows': 0,
            'duplicate_customer_ids': 0,
            'missing_email': 0,
            'missing_name': 0,
            'completeness_pct': 0.0,
        }

    seen_ids = set()
    duplicate_ids = 0
    missing_email = 0
    missing_name = 0
    for row in rows:
        cid = row.get('customer_id', '')
        if cid in seen_ids:
            duplicate_ids += 1
        else:
            seen_ids.add(cid)
        if not (row.get('email') or '').strip():
            missing_email += 1
        if not (row.get('first_name') or '').strip() or not (row.get('last_name') or '').strip():
            missing_name += 1

    issues = duplicate_ids + missing_email + missing_name
    completeness_pct = round(max(0.0, 100.0 - (issues / max(total, 1)) * 100.0), 1)
    return {
        'total_rows': total,
        'duplicate_customer_ids': duplicate_ids,
        'missing_email': missing_email,
        'missing_name': missing_name,
        'completeness_pct': completeness_pct,
    }


@datasets_bp.route('/<dataset_id>/quality-report', methods=['POST'])
@jwt_required()
def regenerate_quality_report(dataset_id):
    """Re-scan the customers table and regenerate the quality report."""
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

    report = _compute_quality_report_from_db(dataset_id)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE datasets SET quality_report = %s WHERE id = %s", (Json(report), dataset_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(username, 'dataset_quality_report_regenerated', f"id={dataset_id} completeness={report['completeness_pct']}%")
    return jsonify(report), 200
