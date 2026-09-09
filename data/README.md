# Data Directory

## Structure

### `/raw`
Raw synthetic data generated from the data generation pipeline.
- CSV exports of generated events, customers, transactions, etc.
- Original, unmodified data before transformation

### `/processed`
Cleaned, validated, and transformed data ready for analysis.
- Data after ETL pipeline
- Feature-engineered datasets
- Aggregated datasets for BI

## Usage

```python
# Load raw data
import pandas as pd
df_raw = pd.read_csv('data/raw/customer_events.csv')

# Load processed data
df_processed = pd.read_parquet('data/processed/customer_360.parquet')
```

## Guidelines

- Never modify raw data files directly
- All transformations should be documented in SQL or Python scripts
- Use Parquet format for processed data (more efficient than CSV)
- Include data dictionaries for each dataset
