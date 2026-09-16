import os
from datetime import datetime, timedelta

import psycopg2

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'customer_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'sushanth123'),
}


def bootstrap_raw_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id VARCHAR(50) PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(100),
                country VARCHAR(100),
                industry VARCHAR(100),
                acquisition_channel VARCHAR(100),
                signup_date TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) NOT NULL,
                event_type VARCHAR(100),
                feature VARCHAR(100),
                event_timestamp TIMESTAMP,
                session_duration_seconds INTEGER,
                event_value DECIMAL(10,2)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) NOT NULL,
                transaction_type VARCHAR(50),
                subscription_plan VARCHAR(100),
                amount DECIMAL(12,2),
                currency VARCHAR(10),
                payment_method VARCHAR(100),
                payment_status VARCHAR(50),
                transaction_timestamp TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) NOT NULL,
                category VARCHAR(100),
                priority VARCHAR(50),
                resolution_time_hours DECIMAL(8,2),
                satisfaction_score INTEGER,
                created_at TIMESTAMP
            )
        ''')
        cur.execute('SELECT COUNT(*) FROM customers')
        if cur.fetchone()[0] == 0:
            for index in range(1, 51):
                cur.execute(
                    '''INSERT INTO customers
                       (customer_id, first_name, last_name, email, country, industry, acquisition_channel, signup_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    (
                        f'CUST_{index:04d}', f'Demo{index}', 'Customer',
                        f'demo{index}@example.com', 'US', 'Technology',
                        'Organic', datetime.now() - timedelta(days=index * 10),
                    ),
                )
        conn.commit()
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    bootstrap_raw_tables()
    from seed_data import seed_database
    seed_database()
    print('[Bootstrap] Database ready')
