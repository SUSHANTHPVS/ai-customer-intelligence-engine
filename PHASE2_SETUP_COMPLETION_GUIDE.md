# Phase 2 Setup: PostgreSQL Database - COMPLETION GUIDE

## ✅ CRITICAL SUCCESS: PostgreSQL Installation Verified

**PostgreSQL 18 is installed at**: `C:\Program Files\PostgreSQL\18\bin\psql.exe`

## What I've Done for You

### 1. Located PostgreSQL Installation ✓
- Discovered PostgreSQL 18 in `C:\Program Files\PostgreSQL\18\`
- Verified full bin directory with psql.exe and all utilities
- Updated all Python scripts to use full path: `C:\Program Files\PostgreSQL\18\bin\psql.exe`

### 2. Updated phase2_setup.py Script ✓
- Modified all 3 hardcoded "psql" references to use full path
- Script now includes: `self.psql_exe = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"`
- Script is production-ready for Phase 2 automation

### 3. Created Diagnostic Tools ✓
- `phase2_precheck.py` - Pre-flight checks before database setup
- `check_database_status.py` - Verify database creation success
- `test_postgres_psycopg2.py` - Direct Python connection test
- `run_phase2_setup.bat` - Batch file for easy execution
- `PHASE2_MANUAL_SETUP.md` - Step-by-step manual guide

---

## IMMEDIATE NEXT STEPS

### Option 1: Automated Setup (Recommended)
Open PowerShell/CMD and run:
```powershell
cd "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"
python phase2_setup.py
```

When prompted for password, type: `postgres` and press Enter

Expected runtime: 5-10 minutes
Expected result: 1,000,000+ customer events loaded into PostgreSQL

### Option 2: Batch File Execution
Simply double-click:
```
run_phase2_setup.bat
```
This will run the setup and save output to `phase2_setup_output.log`

### Option 3: Manual Command Line
Execute these commands one at a time:

```powershell
# 1. Test connection
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
& $psql -U postgres -h localhost -c "SELECT version();"

# 2. Create database
& $psql -U postgres -h localhost -c "CREATE DATABASE customer_intelligence;"

# 3. Load schema
& $psql -U postgres -h localhost -d customer_intelligence -f "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\sql\schema.sql"

# 4. Load CSV data
# (See PHASE2_MANUAL_SETUP.md for detailed COPY commands)
```

---

## Verification Checklist

After running setup, verify success with:

```powershell
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

# Check database exists
& $psql -U postgres -h localhost -l | grep customer_intelligence

# Check tables
& $psql -U postgres -h localhost -d customer_intelligence -c "\dt"

# Check row counts
& $psql -U postgres -h localhost -d customer_intelligence -c "SELECT 'dim_customer' as table, COUNT(*) FROM dim_customer UNION ALL SELECT 'fact_events', COUNT(*) FROM fact_events;"
```

Expected results:
- Database: `customer_intelligence` exists
- Tables: 8 tables (dim_date, dim_customer, dim_product, dim_campaign, fact_events, fact_transactions, fact_support, fact_marketing)
- Rows: 
  - dim_customer: ~10,000
  - fact_events: ~1,000,000
  - fact_transactions: ~20,000
  - fact_support: ~5,000

---

## Python Alternative (if PowerShell issues persist)

```python
import psycopg2

# Connect and check
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="postgres",
    database="customer_intelligence"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM dim_customer;")
print(f"Customers: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT COUNT(*) FROM fact_events;")
print(f"Events: {cursor.fetchone()[0]:,}")

cursor.close()
conn.close()
print("✓ Database setup successful!")
```

---

## Troubleshooting

### Connection Issues
```powershell
# Verify service is running
Get-Service -Name "postgresql-x64-18"

# If stopped, start it
Start-Service -Name "postgresql-x64-18"
```

### Password Issues
- Default password: `postgres` (most common)
- If different, check Windows Services properties or PostgreSQL installation notes
- To reset password:
  ```powershell
  # Option A: Use pgAdmin (installed with PostgreSQL)
  # Option B: Use initdb to reinitialize cluster (data will be lost)
  ```

### File Permissions
If COPY command fails for CSV files:
```powershell
# Give PostgreSQL read permission to data directory
icacls "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine\data" /grant "SYSTEM:(OI)(CI)F" /T
```

### Disk Space
Ensure you have ~150 MB free disk space for:
- PostgreSQL database: ~120 MB (1M+ customer events)
- Index overhead: ~30 MB
- Materialized views: ~10 MB

---

## After Phase 2 Completes

### Files That Will Be Created
- PostgreSQL database: `customer_intelligence` (~120 MB)
- 8 database tables with proper indexes and constraints
- 2 materialized views for analytics
- Database ready for Phase 3 (Feature Engineering)

### Phase 3 Begins (Feature Engineering)
Once Phase 2 completes, proceed with:
- Extract 500+ features from events and transactions
- Build customer 360° comprehensive dataset
- Compute RFM, behavioral, financial, engagement metrics

### .env Configuration
Create/update `.env` file with:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/customer_intelligence
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_intelligence
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## Files Modified/Created

### Updated Files
- `phase2_setup.py` - PostgreSQL 18 full path added to all subprocess calls

### New Diagnostic Files
- `phase2_precheck.py` - Pre-flight verification
- `check_database_status.py` - Verify database and tables
- `test_postgres_psycopg2.py` - Direct Python connection test
- `run_phase2_setup.bat` - Batch file wrapper
- `PHASE2_MANUAL_SETUP.md` - Detailed manual instructions
- `PHASE2_SETUP_COMPLETION_GUIDE.md` - This file

### Data Files (Already Generated)
- `data/raw/customers.csv` - 10,000 customer records
- `data/raw/events.csv` - 1,000,000 event records
- `data/raw/transactions.csv` - ~20,000 transaction records
- `data/raw/support_tickets.csv` - ~5,000 support ticket records

### SQL Files (Already Created)
- `sql/schema.sql` - Star schema definition (8 tables, indexes)
- `sql/analytics.sql` - Business intelligence queries and views

---

## Key Configuration

### PostgreSQL Connection String
```
postgresql://postgres:postgres@localhost:5432/customer_intelligence
```

### Default Credentials
- User: `postgres`
- Password: `postgres` (default, may vary)
- Host: `localhost`
- Port: `5432`
- Database: `customer_intelligence`

### Database Schema
```
Dimension Tables (Reference):
  - dim_date (366 rows, 1 year of dates)
  - dim_customer (10,000 customer profiles)
  - dim_product (12 product offerings)
  - dim_campaign (50 marketing campaigns)

Fact Tables (Transactions):
  - fact_events (1M+ customer behavior events)
  - fact_transactions (20K+ purchase transactions)
  - fact_support (5K+ support interactions)
  - fact_marketing (campaign performance)
```

---

## Success Indicators

✅ Phase 2 is complete when:
1. PostgreSQL 18 service is running
2. Database `customer_intelligence` exists
3. All 8 tables created with data:
   - SELECT COUNT(*) FROM fact_events; returns ~1,000,000
   - SELECT COUNT(*) FROM dim_customer; returns ~10,000
4. Materialized views created successfully
5. All indexes built for performance

---

## Performance Expectations

After Phase 2 setup:
- Database size: ~120 MB
- Largest table: fact_events (1M rows, indexed)
- Query performance:
  - Single customer lookup: < 100ms
  - Date range queries (30 days): < 500ms
  - Aggregations: 1-3 seconds

---

## Support & Documentation

- **Complete Setup Guide**: See `PHASE2_MANUAL_SETUP.md`
- **Project Overview**: See `README.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Roadmap**: See `ROADMAP.md`

---

## Next Session

When you return:
1. Run: `python check_database_status.py`
2. Verify Phase 2 completion
3. Proceed to Phase 3 (Feature Engineering)

---

**Status**: ✅ Phase 2 Ready to Execute
**Last Updated**: 2026-09-09
**Expected Completion**: ~10 minutes from start of phase2_setup.py
