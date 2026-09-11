#!/usr/bin/env python3
"""
Bulk customer CSV import (admin only). Upserts rows into the customers
table; feature tables are refreshed separately by the background jobs.
"""
import csv
import io
import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from rbac import role_required
from audit import get_db_connection, record_audit

logger = logging.getLogger(__name__)
import_bp = Blueprint('import', __name__, url_prefix='/customers')

REQUIRED_COLUMNS = {
    'customer_id', 'first_name', 'last_name', 'email',
    'country', 'industry', 'acquisition_channel', 'signup_date'
}


@import_bp.route('/import', methods=['POST'])
@role_required('admin')
def import_customers():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded (expected multipart field "file")'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only .csv files are supported'}), 400

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
    except UnicodeDecodeError:
        return jsonify({'error': 'File must be UTF-8 encoded'}), 400

    reader = csv.DictReader(stream)
    fieldnames = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - fieldnames
    if missing:
        return jsonify({'error': f"Missing required columns: {', '.join(sorted(missing))}"}), 400

    inserted, updated, errors = 0, 0, []
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for idx, row in enumerate(reader, start=2):
            try:
                cur.execute("""
                    INSERT INTO customers (customer_id, first_name, last_name, email,
                                            country, industry, acquisition_channel, signup_date, dataset_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'default')
                    ON CONFLICT (customer_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        email = EXCLUDED.email,
                        country = EXCLUDED.country,
                        industry = EXCLUDED.industry,
                        acquisition_channel = EXCLUDED.acquisition_channel,
                        signup_date = EXCLUDED.signup_date
                    RETURNING (xmax = 0) AS inserted
                """, (
                    row['customer_id'], row['first_name'], row['last_name'], row['email'],
                    row['country'], row['industry'], row['acquisition_channel'], row['signup_date']
                ))
                was_insert = cur.fetchone()[0]
                if was_insert:
                    inserted += 1
                else:
                    updated += 1
            except Exception as e:
                conn.rollback()
                errors.append(f"Row {idx}: {str(e)}")
                continue

        conn.commit()
    finally:
        cur.close()
        conn.close()

    record_audit(
        get_jwt_identity(), 'customers_imported',
        f"inserted={inserted} updated={updated} errors={len(errors)}"
    )

    return jsonify({
        'inserted': inserted,
        'updated': updated,
        'errors': errors[:20],
        'total_errors': len(errors),
    }), 200
