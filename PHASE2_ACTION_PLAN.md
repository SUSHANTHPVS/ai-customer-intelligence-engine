# Phase 2: PostgreSQL Data Warehouse Setup - Action Plan

**Status:** Ready to execute (PostgreSQL installation required)
**Date:** 2026-09-09

## Current State

✅ **Completed:**
- Synthetic data generated (10K customers, 1M+ events)
- PostgreSQL schema designed
- Analytics queries written
- Phase 2 automation script created

❌ **Pending:**
- PostgreSQL installation on system
- Database creation and schema loading
- Data ingestion from CSV files

---

## Immediate Actions Required

### Step 1: Install PostgreSQL (REQUIRED)

**Choose ONE installation method:**

#### Option A: Chocolatey (if installed)
```powershell
choco install postgresql
```

#### Option B: Winget (Windows 10/11+)
```powershell
winget install PostgreSQL.PostgreSQL
```

#### Option C: Manual Download
1. Visit: https://www.postgresql.org/download/windows/
2. Download PostgreSQL 14 or 15 LTS
3. Run installer with these settings:
   - **Password for 'postgres' user:** (set a secure password)
   - **Port:** 5432 (default)
   - **Components:** Check "pgAdmin"
4. Finish installation
5. Restart your terminal

#### Option D: Docker (if Docker is installed)
```powershell
docker run --name customer-intel-db `
  -e POSTGRES_PASSWORD=postgres `
  -p 5432:5432 `
  -d postgres:15
```

### Step 2: Verify PostgreSQL Installation

After installation, verify in PowerShell:
```powershell
psql --version
```

Expected output:
```
psql (PostgreSQL) 14.x or higher
```

---

### Step 3: Run Phase 2 Automation Script

Once PostgreSQL is installed and verified:

```powershell
cd "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"
python phase2_setup.py
```

**The script will:**
1. ✓ Check PostgreSQL connectivity
2. ✓ Create `customer_intelligence` database
3. ✓ Load schema from `sql/schema.sql`
4. ✓ Load data from CSV files
5. ✓ Create materialized views
6. ✓ Validate all tables
7. ✓ Display data summary

**Expected runtime:** 5-10 minutes (depending on hardware)

---

## Environment Configuration

After PostgreSQL is installed, create `.env` file:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/customer_intelligence
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_intelligence
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD

# Data Generation
SYNTHETIC_DATA_SIZE=1000000
CUSTOMERS_COUNT=10000
DATE_RANGE_DAYS=365

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

Replace `YOUR_PASSWORD` with the password set during PostgreSQL installation.

---

## Expected Results

After Phase 2 completion:

### Database Structure
```
customer_intelligence
├── Dimensions (dm_*)
│   ├── dim_date (366 rows)
│   ├── dim_customer (10,000 rows)
│   ├── dim_product (12 rows)
│   └── dim_campaign (50 rows)
├── Facts (fact_*)
│   ├── fact_events (1,000,000+ rows)
│   ├── fact_transactions (~200,000 rows)
│   ├── fact_support (~50,000 rows)
│   └── fact_marketing (~100,000 rows)
└── Views
    └── v_customer_metrics (materialized)
```

### Verification Queries

```sql
-- View all tables
\dt

-- Check record counts
SELECT COUNT(*) FROM dim_customer;        -- 10,000
SELECT COUNT(*) FROM fact_events;         -- 1,000,000+
SELECT COUNT(*) FROM fact_transactions;   -- ~200,000
SELECT COUNT(*) FROM fact_support;        -- ~50,000

-- Sample customer data
SELECT * FROM dim_customer LIMIT 5;

-- Sample event data
SELECT * FROM fact_events LIMIT 5;
```

---

## Troubleshooting

### PostgreSQL won't start
- Check Windows Services: `services.msc` → Look for "postgresql-x64-15" or similar
- If not running, right-click and select "Start"

### Connection refused error
- Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Check port 5432 is not blocked by firewall
- Verify credentials (default user: `postgres`)

### Script asks for password
- The default password is typically `postgres` (set during installation)
- If you forgot it, reinstall PostgreSQL and set a new password

### Out of memory during data loading
- Reduce `SYNTHETIC_DATA_SIZE` in `.env` file
- Or load data in batches instead of all at once

### Schema load fails
- Check `sql/schema.sql` file exists and is valid
- Verify PostgreSQL version is 14+
- Check for conflicting table names

---

## Phase 2 Deliverables

**By end of Phase 2, you will have:**

1. ✓ PostgreSQL database running
2. ✓ Star schema deployed (8 tables + indexes)
3. ✓ 1M+ customer behavior records loaded
4. ✓ Materialized views for analytics
5. ✓ Database queries ready for Phase 3

---

## Next Phase: Phase 3 (Week 2-3)

After Phase 2 completion, Phase 3 will focus on:
- Feature engineering (500+ behavioral, financial, temporal features)
- Customer 360° dataset creation
- Churn indicators and risk scoring

---

## Support Files

- `phase2_setup.py` - Automated setup script (ready to run)
- `POSTGRES_SETUP.txt` - Installation guide (printed during setup)
- `sql/schema.sql` - Database schema definition
- `sql/analytics.sql` - Analytics queries and views
- `data/raw/*.csv` - Synthetic data files

---

**NEXT: Install PostgreSQL and run `python phase2_setup.py`**
