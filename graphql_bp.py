#!/usr/bin/env python3
"""
Read-only GraphQL API (Ariadne) alongside the REST endpoints, offering
flexible, client-shaped queries over customers and segmentation data.
"""
import logging

from ariadne import QueryType, make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor

from audit import get_db_connection
from datasets_bp import get_active_dataset_id

logger = logging.getLogger(__name__)
graphql_bp = Blueprint('graphql', __name__, url_prefix='/graphql')

type_defs = """
    type Customer {
        customerId: String!
        firstName: String
        lastName: String
        email: String
        country: String
        segment: String
        riskLevel: String
        engagementScore: Float
        lifetimeValue: Float
    }

    type SegmentCount {
        segment: String!
        count: Int!
    }

    type Query {
        customer(customerId: String!): Customer
        customers(search: String, segment: String, riskLevel: String, limit: Int = 10): [Customer!]!
        segmentation: [SegmentCount!]!
    }
"""

query = QueryType()

CUSTOMER_SELECT = """
    SELECT c.customer_id, c.first_name, c.last_name, c.email, c.country,
           fe.segment, fe.engagement_score, fc.risk_level, fr.lifetime_value
    FROM customers c
    LEFT JOIN feature_engagement fe ON c.customer_id = fe.customer_id
    LEFT JOIN feature_churn_risk fc ON c.customer_id = fc.customer_id
    LEFT JOIN feature_rfm fr ON c.customer_id = fr.customer_id
"""


def _row_to_customer(row):
    if not row:
        return None
    return {
        'customerId': row['customer_id'],
        'firstName': row['first_name'],
        'lastName': row['last_name'],
        'email': row['email'],
        'country': row['country'],
        'segment': row['segment'],
        'riskLevel': row['risk_level'],
        'engagementScore': float(row['engagement_score']) if row['engagement_score'] is not None else None,
        'lifetimeValue': float(row['lifetime_value']) if row['lifetime_value'] is not None else None,
    }


@query.field('customer')
def resolve_customer(_, info, customerId):
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(f"{CUSTOMER_SELECT} WHERE c.customer_id = %s AND c.dataset_id = %s", (customerId, dataset_id))
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    return _row_to_customer(row)


@query.field('customers')
def resolve_customers(_, info, search=None, segment=None, riskLevel=None, limit=10):
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conditions = ["c.dataset_id = %s"]
    params = [dataset_id]
    if search:
        like = f"%{search}%"
        conditions.append("(c.customer_id ILIKE %s OR c.first_name ILIKE %s OR c.last_name ILIKE %s)")
        params.extend([like, like, like])
    if segment:
        conditions.append("fe.segment = %s")
        params.append(segment)
    if riskLevel:
        conditions.append("fc.risk_level = %s")
        params.append(riskLevel)
    where_clause = f"WHERE {' AND '.join(conditions)}"

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            f"{CUSTOMER_SELECT} {where_clause} ORDER BY c.customer_id LIMIT %s",
            params + [min(int(limit or 10), 100)]
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return [_row_to_customer(r) for r in rows]


@query.field('segmentation')
def resolve_segmentation(_, info):
    dataset_id = get_active_dataset_id(get_jwt_identity())
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT segment, COUNT(*) as count FROM feature_engagement WHERE dataset_id = %s GROUP BY segment", (dataset_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return [{'segment': r['segment'], 'count': r['count']} for r in rows]


schema = make_executable_schema(type_defs, query)
explorer_html = ExplorerGraphiQL().html(None)


@graphql_bp.route('', methods=['GET'])
def graphql_playground():
    return explorer_html, 200


@graphql_bp.route('', methods=['POST'])
@jwt_required()
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=request, debug=False)
    return jsonify(result), 200 if success else 400
