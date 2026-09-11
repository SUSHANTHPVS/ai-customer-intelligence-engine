# Phase 2: PostgreSQL Database Setup - Manual Guide

## ✓ Status: PostgreSQL 18 Installed Successfully
- **Location**: `C:\Program Files\PostgreSQL\18\bin\psql.exe`
- **Installation Verified**: Via file system directory listing
- **Version**: PostgreSQL 18 (latest version)

## Quick Start (Automated)

### Step 1: Open PowerShell and Navigate to Project
```powershell
cd "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"
```

### Step 2: Run Phase 2 Setup Automation
```powershell
python phase2_setup.py
```

**When prompted for password, enter**: `postgres` (default PostgreSQL password)

Expected output:
```
[1/8] Checking PostgreSQL installation...
      OK - PostgreSQL found at C:\Program Files\PostgreSQL\18\bin\psql.exe
      Version: PostgreSQL 18.x.x...

[2/8] Creating database 'customer_intelligence'...
      OK - Database created

[3/8] Loading schema (dim_date, dim_customer, fact_events, etc.)...
      OK - Schema loaded

[4/8] Loading CSV data...
      Loading customers.csv (10,000 rows)... OK
      Loading events.csv (1,000,000 rows)... OK
      Loading transactions.csv (~20K rows)... OK
      Loading support_tickets.csv (~5K rows)... OK

[5/8] Creating materialized views...
      OK - Analytics views created

[6/8] Validating tables...
      ✓ All tables present with data

[7/8] Generating summary...
      Database: customer_intelligence
      Tables: 8 (dim_date, dim_customer, dim_product, dim_campaign, fact_events, fact_transactions, fact_support, fact_marketing)
      Total records: 1,015,000+

[8/8] Setup complete!
      ✓ Phase 2 Complete - Ready for Phase 3 (Feature Engineering)
```

---

## Manual Verification Steps

If you want to verify the setup manually without running the script:

### Option A: Using psql Command Line

```powershell
# Test connection
psql -U postgres -h localhost -c "SELECT version();"

# List databases
psql -U postgres -h localhost -l

# Connect to customer_intelligence database
psql -U postgres -h localhost -d customer_intelligence

# Inside psql, run these commands:
SELECT COUNT(*) FROM dim_customer;        -- Should show ~10,000
SELECT COUNT(*) FROM fact_events;         -- Should show ~1,000,000
SELECT COUNT(*) FROM dim_date;            -- Should show ~366
\dt                                       -- List all tables
```

### Option B: Using Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="postgres",
    database="customer_intelligence"
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM dim_customer;")
print(f"Customers: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM fact_events;")
print(f"Events: {cur.fetchone()[0]:,}")

conn.close()
```

---

## Troubleshooting

### Issue: "psql: command not found" or "system cannot find the file specified"

**Solution**: Use full path
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "SELECT version();"
```

### Issue: "password authentication failed"

**Solutions**:
1. Try default password: `postgres`
2. If different password was set during installation, use that password
3. Check Windows Services for PostgreSQL:
   ```powershell
   Get-Service -Name "postgresql-x64-18" | Select-Object Status
   ```

### Issue: "could not connect to server: Connection refused"

**Solution**: Start PostgreSQL service
```powershell
Start-Service -Name "postgresql-x64-18"
# Or use Windows Services panel
```

### Issue: "database customer_intelligence does not exist"

**Solution**: Run phase2_setup.py to create it, or manually:
```powershell
psql -U postgres -h localhost -c "CREATE DATABASE customer_intelligence;"
```

---

## What Gets Created

### Database: `customer_intelligence`

#### Dimension Tables (Reference Data)
- **dim_date**: 366 rows (one year of dates)
- **dim_customer**: 10,000 rows (customer profiles)
- **dim_product**: 12 rows (product catalog)
- **dim_campaign**: 50 rows (marketing campaigns)

#### Fact Tables (Transaction Data)
- **fact_events**: 1,000,000+ rows (customer behavior events)
- **fact_transactions**: ~20,000 rows (purchase transactions)
- **fact_support**: ~5,000 rows (customer support tickets)
- **fact_marketing**: Campaign performance data

#### Materialized Views
- **v_customer_metrics**: Aggregate metrics per customer
- Additional views for analytics and reporting

---

## Next Steps After Phase 2 Completion

### Phase 3: Feature Engineering
- Extract 500+ features from raw events and transactions
- Create customer 360° comprehensive dataset
- Compute engagement, financial, behavioral metrics

### Phase 4: Machine Learning Model Training
- Train churn prediction models (Logistic Regression, XGBoost, LightGBM)
- Revenue risk scoring models
- Generate model explanations (SHAP values)

### Phase 5: Model Serving API
- Deploy ML models as REST endpoints
- Real-time predictions for new customers
- Batch prediction capabilities

### Phase 6: Analytics Dashboard
- Customer churn probability visualization
- Revenue at risk by segment
- Cohort analysis and retention curves
- Campaign ROI analysis

---

## Environment Configuration

Create `.env` file in project root with:
```
# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/customer_intelligence
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_intelligence
DB_USER=postgres
DB_PASSWORD=postgres

# ML Models
MODEL_PATH=./models
FEATURE_STORE=./data/features

# API
API_PORT=8000
API_HOST=0.0.0.0
```

---

## Performance Notes

- `fact_events` table (1M+ rows) is indexed on:
  - customer_id (for fast customer queries)
  - event_timestamp (for date range queries)
  - event_type (for event filtering)
  
- Expected query times:
  - Single customer: < 100ms
  - 1-month date range: < 500ms
  - Full table scan: 2-5 seconds (depending on disk)

---

## Support

If Phase 2 setup encounters issues:

1. Run: `python check_database_status.py` to verify current state
2. Check PostgreSQL service status: Services app or `Get-Service postgresql-x64-18`
3. Verify CSV files exist: `data/raw/*.csv` (should be ~115 MB total)
4. Ensure psql path is correct: `C:\Program Files\PostgreSQL\18\bin\psql.exe`

For questions or issues, refer to the complete ARCHITECTURE.md and README.md files.
