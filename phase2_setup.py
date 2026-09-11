#!/usr/bin/env python3
"""
Phase 2: PostgreSQL Warehouse Setup Automation
Automates database creation, schema loading, and data ingestion
"""

import subprocess
import os
import sys
from pathlib import Path
import time

class Phase2Setup:
    def __init__(self, db_user="postgres", db_password="postgres", db_host="localhost", db_port=5432):
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = "customer_intelligence"
        self.project_root = Path(r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine")
        # PostgreSQL 18 installation path
        self.psql_exe = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
        
    def run_psql_command(self, command, database=None):
        """Execute a psql command"""
        try:
            cmd = [
                self.psql_exe,
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user
            ]
            
            if database:
                cmd.extend(["-d", database])
            
            cmd.extend(["-c", command])
            
            # Set password via environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
            
        except Exception as e:
            return False, "", str(e)
    
    def run_psql_file(self, filepath, database=None):
        """Execute a SQL file"""
        try:
            cmd = [
                self.psql_exe,
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user
            ]
            
            if database:
                cmd.extend(["-d", database])
            
            cmd.extend(["-f", str(filepath)])
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
            return result.returncode == 0, result.stdout, result.stderr
            
        except Exception as e:
            return False, "", str(e)
    
    def check_postgresql(self):
        """Check if PostgreSQL is installed and accessible"""
        print("\n[1/8] Checking PostgreSQL installation...")
        success, stdout, stderr = self.run_psql_command("SELECT version();")
        
        if success:
            print("      OK - PostgreSQL is accessible")
            # Extract version from output
            if "PostgreSQL" in stdout:
                for line in stdout.split("\n"):
                    if "PostgreSQL" in line:
                        print(f"      {line.strip()}")
                        break
            return True
        else:
            print("      ERROR - Cannot connect to PostgreSQL")
            print(f"      Make sure PostgreSQL is running on {self.db_host}:{self.db_port}")
            print(f"      Error: {stderr}")
            return False
    
    def create_database(self):
        """Create the customer_intelligence database"""
        print("\n[2/8] Creating database 'customer_intelligence'...")
        
        # Check if database exists
        success, stdout, stderr = self.run_psql_command(
            f"SELECT 1 FROM pg_database WHERE datname='{self.db_name}';"
        )
        
        if "1 row" in stdout or "1 row" in stdout:
            print("      Database already exists")
            return True
        
        # Create database
        success, stdout, stderr = self.run_psql_command(
            f"CREATE DATABASE {self.db_name};"
        )
        
        if success or "already exists" in stderr:
            print(f"      OK - Database created")
            return True
        else:
            print(f"      ERROR - Failed to create database")
            print(f"      {stderr}")
            return False
    
    def load_schema(self):
        """Load the database schema from sql/schema.sql"""
        print("\n[3/8] Loading database schema...")
        
        schema_file = self.project_root / "sql" / "schema.sql"
        
        if not schema_file.exists():
            print(f"      ERROR - Schema file not found: {schema_file}")
            return False
        
        success, stdout, stderr = self.run_psql_file(str(schema_file), self.db_name)
        
        if success:
            print("      OK - Schema loaded")
            # Count tables
            table_count = stdout.count("CREATE TABLE")
            if table_count > 0:
                print(f"      Created {table_count} tables")
            return True
        else:
            print("      ERROR - Failed to load schema")
            print(f"      {stderr}")
            return False
    
    def load_data(self):
        """Load CSV data into the database"""
        print("\n[4/8] Loading data from CSV files...")
        
        data_dir = self.project_root / "data" / "raw"
        
        if not data_dir.exists():
            print(f"      ERROR - Data directory not found: {data_dir}")
            return False
        
        # Map CSV files to table names with explicit column specifications
        csv_files = {
            "customers.csv": {
                "table": "customers",
                "columns": "(customer_id, first_name, last_name, email, country, industry, acquisition_channel, signup_date)"
            },
            "events.csv": {
                "table": "events",
                "columns": "(event_id, customer_id, event_type, feature, event_timestamp, session_duration_seconds, event_value)"
            },
            "transactions.csv": {
                "table": "transactions",
                "columns": "(transaction_id, customer_id, transaction_type, subscription_plan, amount, currency, payment_method, payment_status, transaction_timestamp)"
            },
            "support_tickets.csv": {
                "table": "support_tickets",
                "columns": "(ticket_id, customer_id, category, priority, resolution_time_hours, satisfaction_score, created_at)"
            },
        }
        
        all_loaded = True
        
        for csv_file, file_config in csv_files.items():
            csv_path = data_dir / csv_file
            table_name = file_config["table"]
            columns = file_config["columns"]
            
            if not csv_path.exists():
                print(f"      SKIP - {csv_file} not found")
                all_loaded = False
                continue
            
            # Count rows in CSV
            try:
                with open(csv_path) as f:
                    row_count = sum(1 for _ in f) - 1  # Exclude header
                print(f"      Loading {csv_file} ({row_count:,} rows)...")
            except:
                print(f"      Loading {csv_file}...")
            
            # Create COPY command using absolute file path with explicit column specification
            # Convert to Windows-friendly format with backslashes
            abs_path = str(csv_path.resolve()).replace('\\', '\\\\')
            copy_sql = f"\\COPY {table_name} {columns} FROM '{abs_path}' WITH (FORMAT csv, HEADER true);"
            
            try:
                cmd = [
                    self.psql_exe,
                    "-h", self.db_host,
                    "-p", str(self.db_port),
                    "-U", self.db_user,
                    "-d", self.db_name,
                    "-c", copy_sql
                ]
                
                env = os.environ.copy()
                env['PGPASSWORD'] = self.db_password
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120
                )
                
                if result.returncode == 0:
                    print(f"      OK - {csv_file} loaded")
                else:
                    print(f"      ERROR - Failed to load {csv_file}")
                    if result.stderr:
                        print(f"      {result.stderr[:200]}")
                    all_loaded = False
                        
            except Exception as e:
                print(f"      ERROR - Exception loading {csv_file}: {e}")
                all_loaded = False
        
        return all_loaded
    
    def create_materialized_views(self):
        """Create and refresh materialized views for analytics"""
        print("\n[5/8] Creating materialized views...")
        
        analytics_file = self.project_root / "sql" / "analytics.sql"
        
        if not analytics_file.exists():
            print(f"      SKIP - Analytics file not found: {analytics_file}")
            return True
        
        success, stdout, stderr = self.run_psql_file(str(analytics_file), self.db_name)
        
        if success:
            print("      OK - Materialized views created")
            
            # Refresh views to populate them with data
            print("      Refreshing materialized views...")
            refresh_sql = """
            REFRESH MATERIALIZED VIEW v_customer_summary;
            REFRESH MATERIALIZED VIEW v_events_daily;
            REFRESH MATERIALIZED VIEW v_revenue_analytics;
            REFRESH MATERIALIZED VIEW v_support_analytics;
            """
            
            success, stdout, stderr = self.run_psql_command(refresh_sql, self.db_name)
            if success:
                print("      OK - Materialized views refreshed")
            else:
                print("      WARN - Views may not be fully refreshed")
            
            return True
        else:
            print("      WARN - Some views may have failed")
            if stderr and len(stderr) < 500:
                print(f"      {stderr}")
            return True  # Don't fail on this, as some views might already exist
    
    def validate_tables(self):
        """Validate that all required tables exist"""
        print("\n[6/8] Validating database tables...")
        
        required_tables = [
            "customers",
            "events",
            "transactions",
            "support_tickets",
        ]
        
        success, stdout, stderr = self.run_psql_command(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;",
            self.db_name
        )
        
        if not success:
            print("      ERROR - Failed to query tables")
            return False
        
        found_tables = [line.strip() for line in stdout.split("\n") if line.strip() and line.strip() != "tablename"]
        
        print(f"      Found {len(found_tables)} tables:")
        for table in found_tables:
            status = "OK" if table in required_tables else "EXTRA"
            print(f"        - {table} ({status})")
        
        missing = set(required_tables) - set(found_tables)
        if missing:
            print(f"      WARN - Missing tables: {missing}")
            return False
        
        return True
    
    def get_data_summary(self):
        """Get summary statistics on loaded data"""
        print("\n[7/8] Data Summary:")
        
        queries = [
            ("Customers", "SELECT COUNT(*) FROM customers;"),
            ("Events", "SELECT COUNT(*) FROM events;"),
            ("Transactions", "SELECT COUNT(*) FROM transactions;"),
            ("Support Tickets", "SELECT COUNT(*) FROM support_tickets;"),
        ]
        
        for name, query in queries:
            success, stdout, stderr = self.run_psql_command(query, self.db_name)
            
            if success:
                # Extract count from output
                for line in stdout.split("\n"):
                    if line.strip() and line.strip() != "count":
                        try:
                            count = int(line.strip())
                            print(f"        {name}: {count:,} records")
                        except:
                            pass
    
    def run_setup(self):
        """Run the complete Phase 2 setup"""
        print("\n" + "=" * 70)
        print("PHASE 2: PostgreSQL Data Warehouse Setup")
        print("=" * 70)
        
        print(f"Target: {self.db_name} @ {self.db_host}:{self.db_port}")
        print(f"User: {self.db_user}")
        
        # Run all steps
        steps = [
            ("PostgreSQL Check", self.check_postgresql),
            ("Database Creation", self.create_database),
            ("Schema Loading", self.load_schema),
            ("Data Loading", self.load_data),
            ("Materialized Views", self.create_materialized_views),
            ("Table Validation", self.validate_tables),
            ("Data Summary", self.get_data_summary),
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
                else:
                    print(f"\n*** Setup failed at: {step_name} ***")
                    break
            except Exception as e:
                print(f"\n*** Unexpected error in {step_name}: {e} ***")
                break
        
        print("\n" + "=" * 70)
        if success_count == len(steps):
            print("SUCCESS - Phase 2 setup completed!")
            print("\nNext steps:")
            print("  1. Review PHASE1_COMPLETE.md for Phase 3 tasks")
            print("  2. Proceed with feature engineering")
            print("  3. Start Phase 3: Feature Engineering (Week 2-3)")
        else:
            print(f"PARTIAL - Completed {success_count}/{len(steps)} steps")
            print("Please review errors above and retry")
        print("=" * 70 + "\n")
        
        return success_count == len(steps)


if __name__ == "__main__":
    # Configuration
    db_user = "postgres"
    
    # Get password from environment or use default
    db_password = os.environ.get('PGPASSWORD', 'sushanth123')
    
    setup = Phase2Setup(
        db_user=db_user,
        db_password=db_password,
        db_host="localhost",
        db_port=5432
    )
    
    success = setup.run_setup()
    sys.exit(0 if success else 1)
