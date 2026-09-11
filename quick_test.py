import psycopg2
try:
    conn = psycopg2.connect(host="localhost", user="postgres", password="postgres")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("✓ PostgreSQL connection successful")
    print(cur.fetchone()[0][:80])
except Exception as e:
    print(f"✗ Error: {e}")
