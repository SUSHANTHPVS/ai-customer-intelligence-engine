#!/usr/bin/env python3
"""
Background job scheduling (APScheduler).
Periodically recomputes lightweight aggregate snapshots and warms
the Redis cache so dashboard reads stay fast, with a status endpoint
for observability.
"""
import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from psycopg2.extras import RealDictCursor, Json

from cache import cache_set, cache_get, cache_delete_pattern

logger = logging.getLogger(__name__)
jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}

scheduler = BackgroundScheduler()
_job_history = []


def _record_run(job_name, status, detail=''):
    entry = {
        'job': job_name,
        'status': status,
        'detail': detail,
        'ran_at': datetime.now(timezone.utc).isoformat(),
    }
    _job_history.insert(0, entry)
    del _job_history[20:]
    cache_set('jobs:last_run', entry, ttl=3600)


def refresh_risk_snapshot():
    """Recompute churn-risk distribution per dataset and invalidate stale cache entries."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id FROM datasets WHERE status = 'ready'")
        dataset_ids = [row['id'] for row in cur.fetchall()]

        summary = {}
        for dataset_id in dataset_ids:
            cur.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM feature_churn_risk
                WHERE dataset_id = %s
                GROUP BY risk_level
            """, (dataset_id,))
            snapshot = {row['risk_level']: row['count'] for row in cur.fetchall()}
            cache_set(f'stats:risk_snapshot:{dataset_id}', snapshot, ttl=300)
            summary[dataset_id] = snapshot

        cur.close()
        conn.close()

        cache_delete_pattern('analytics:churn-risk*')
        _record_run('refresh_risk_snapshot', 'success', str(summary))
        logger.info(f"[Jobs] refresh_risk_snapshot completed for {len(dataset_ids)} dataset(s)")
    except Exception as e:
        _record_run('refresh_risk_snapshot', 'failed', str(e))
        logger.error(f"[Jobs] refresh_risk_snapshot failed: {e}")


def _run_scheduled_retraining():
    """Retrain eligible datasets on a daily cadence and persist refreshed metrics."""
    try:
        from ml_bp import train_churn_model

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, name, status FROM datasets WHERE status = 'ready'")
        datasets = cur.fetchall()

        for dataset in datasets:
            metrics = train_churn_model(dataset['id'])
            if 'error' in metrics:
                _record_run('scheduled_retraining', 'skipped', f"{dataset['id']}: {metrics['error']}")
                continue

            cur2 = conn.cursor()
            cur2.execute(
                "UPDATE datasets SET model_metrics = %s WHERE id = %s",
                (Json(metrics), dataset['id'])
            )
            conn.commit()
            cur2.close()
            _record_run('scheduled_retraining', 'success', f"{dataset['id']} -> {metrics.get('model_name', 'churn_model')}")

        cur.close()
        conn.close()
        logger.info(f"[Jobs] scheduled_retraining completed for {len(datasets)} dataset(s)")
    except Exception as e:
        _record_run('scheduled_retraining', 'failed', str(e))
        logger.error(f"[Jobs] scheduled_retraining failed: {e}")


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(
        refresh_risk_snapshot, 'interval', seconds=60,
        id='refresh_risk_snapshot', next_run_time=datetime.now()
    )
    scheduler.add_job(
        _run_generate_insights, 'interval', minutes=5,
        id='generate_insights', next_run_time=datetime.now()
    )
    scheduler.add_job(
        _run_scheduled_retraining, 'interval', hours=24,
        id='scheduled_retraining', next_run_time=datetime.now()
    )
    scheduler.start()
    logger.info("[Jobs] Background scheduler started (refresh_risk_snapshot every 60s, generate_insights every 5m, scheduled_retraining every 24h)")


def _run_generate_insights():
    try:
        from insights import generate_insights
        generate_insights()
        _record_run('generate_insights', 'success')
    except Exception as e:
        _record_run('generate_insights', 'failed', str(e))
        logger.error(f"[Jobs] generate_insights failed: {e}")


@jobs_bp.route('/status', methods=['GET'])
@jwt_required(optional=True)
def job_status():
    from datasets_bp import get_active_dataset_id
    dataset_id = get_active_dataset_id(get_jwt_identity())
    jobs = [
        {'id': job.id, 'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None}
        for job in scheduler.get_jobs()
    ]
    return jsonify({
        'scheduler_running': scheduler.running,
        'jobs': jobs,
        'history': _job_history[:10],
        'risk_snapshot': cache_get(f'stats:risk_snapshot:{dataset_id}'),
    }), 200
