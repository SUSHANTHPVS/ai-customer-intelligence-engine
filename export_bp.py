#!/usr/bin/env python3
"""
CSV/PDF export blueprint for customer lists and analytics summary reports.
"""
import csv
import io
import logging
import os

from flask import Blueprint, Response, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import psycopg2
from psycopg2.extras import RealDictCursor

from audit import record_audit
from datasets_bp import get_active_dataset_id

logger = logging.getLogger(__name__)
export_bp = Blueprint('export', __name__, url_prefix='/export')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123')
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@export_bp.route('/customers.csv', methods=['GET'])
@jwt_required()
def export_customers():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    segment = request.args.get('segment', '').strip().upper()
    risk_level = request.args.get('risk_level', '').strip().upper()

    conditions = ["c.dataset_id = %s"]
    params = [dataset_id]
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
            SELECT c.customer_id, c.first_name, c.last_name, c.email, c.country,
                   fe.segment, fe.engagement_score, fc.risk_level, fc.churn_risk_score,
                   fr.lifetime_value, frev.total_revenue
            FROM customers c
            LEFT JOIN feature_engagement fe ON c.customer_id = fe.customer_id
            LEFT JOIN feature_churn_risk fc ON c.customer_id = fc.customer_id
            LEFT JOIN feature_rfm fr ON c.customer_id = fr.customer_id
            LEFT JOIN feature_revenue frev ON c.customer_id = frev.customer_id
            {where_clause}
            ORDER BY c.customer_id
        """, params)
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    record_audit(get_jwt_identity(), 'export_customers_csv', f"segment={segment} risk_level={risk_level} rows={len(rows)}")

    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=customers_export.csv'}
    )


@export_bp.route('/customers.xlsx', methods=['GET'])
@jwt_required()
def export_customers_xlsx():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    segment = request.args.get('segment', '').strip().upper()
    risk_level = request.args.get('risk_level', '').strip().upper()

    conditions = ["c.dataset_id = %s"]
    params = [dataset_id]
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
            SELECT c.customer_id, c.first_name, c.last_name, c.email, c.country,
                   fe.segment, fe.engagement_score, fc.risk_level, fc.churn_risk_score,
                   fr.lifetime_value, frev.total_revenue
            FROM customers c
            LEFT JOIN feature_engagement fe ON c.customer_id = fe.customer_id
            LEFT JOIN feature_churn_risk fc ON c.customer_id = fc.customer_id
            LEFT JOIN feature_rfm fr ON c.customer_id = fr.customer_id
            LEFT JOIN feature_revenue frev ON c.customer_id = frev.customer_id
            {where_clause}
            ORDER BY c.customer_id
        """, params)
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    headers = list(rows[0].keys()) if rows else [
        'customer_id', 'first_name', 'last_name', 'email', 'country',
        'segment', 'engagement_score', 'risk_level', 'churn_risk_score',
        'lifetime_value', 'total_revenue'
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = 'Customers'
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    for row in rows:
        ws.append([row[h] if row[h] is not None else '' for h in headers])

    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    record_audit(get_jwt_identity(), 'export_customers_xlsx', f"segment={segment} risk_level={risk_level} rows={len(rows)}")

    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='customers_export.xlsx'
    )


@export_bp.route('/analytics-report.csv', methods=['GET'])
@jwt_required()
def export_analytics_report():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT segment, COUNT(*) as count FROM feature_engagement WHERE dataset_id = %s GROUP BY segment", (dataset_id,))
        segments = cur.fetchall()

        cur.execute("SELECT risk_level, COUNT(*) as count FROM feature_churn_risk WHERE dataset_id = %s GROUP BY risk_level", (dataset_id,))
        risk = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Report Section', 'Category', 'Count'])
    for row in segments:
        writer.writerow(['Customer Segmentation', row['segment'], row['count']])
    for row in risk:
        writer.writerow(['Churn Risk', row['risk_level'], row['count']])

    record_audit(get_jwt_identity(), 'export_analytics_report_csv')

    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=analytics_report.csv'}
    )


@export_bp.route('/analytics-report.pdf', methods=['GET'])
@jwt_required()
def export_analytics_report_pdf():
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT segment, COUNT(*) as count FROM feature_engagement WHERE dataset_id = %s GROUP BY segment ORDER BY count DESC", (dataset_id,))
        segments = cur.fetchall()

        cur.execute("SELECT risk_level, COUNT(*) as count FROM feature_churn_risk WHERE dataset_id = %s GROUP BY risk_level", (dataset_id,))
        risk = cur.fetchall()

        cur.execute("""
            SELECT ROUND(AVG(lifetime_value), 2) as avg_ltv, ROUND(AVG(predicted_ltv), 2) as avg_predicted_ltv,
                   COUNT(*) as total_customers
            FROM feature_rfm WHERE dataset_id = %s
        """, (dataset_id,))
        ltv = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph('AI Customer Intelligence Engine', styles['Title']),
        Paragraph('Analytics Summary Report', styles['Heading2']),
        Spacer(1, 12),
        Paragraph(f"Total customers analyzed: {ltv['total_customers']}", styles['Normal']),
        Paragraph(f"Average lifetime value: ${ltv['avg_ltv']} (predicted: ${ltv['avg_predicted_ltv']})", styles['Normal']),
        Spacer(1, 16),
        Paragraph('Customer Segmentation', styles['Heading3']),
    ]

    seg_table_data = [['Segment', 'Customers']] + [[row['segment'], row['count']] for row in segments]
    seg_table = Table(seg_table_data, hAlign='LEFT')
    seg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(seg_table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph('Churn Risk Distribution', styles['Heading3']))

    risk_table_data = [['Risk Level', 'Customers']] + [[row['risk_level'], row['count']] for row in risk]
    risk_table = Table(risk_table_data, hAlign='LEFT')
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b91c1c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(risk_table)

    doc.build(elements)
    buffer.seek(0)

    record_audit(get_jwt_identity(), 'export_analytics_report_pdf')

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='analytics_report.pdf'
    )
