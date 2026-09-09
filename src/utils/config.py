"""
Global configuration for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
SQL_DIR = PROJECT_ROOT / 'sql'

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/customer_intelligence')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'customer_intelligence')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# Data generation configuration
SYNTHETIC_DATA_SIZE = int(os.getenv('SYNTHETIC_DATA_SIZE', 1000000))
CUSTOMERS_COUNT = int(os.getenv('CUSTOMERS_COUNT', 10000))
DATE_RANGE_DAYS = int(os.getenv('DATE_RANGE_DAYS', 365))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

print(f"""
Configuration Loaded:
- Environment: {ENVIRONMENT}
- Database: {DB_NAME} @ {DB_HOST}:{DB_PORT}
- Data Size: {SYNTHETIC_DATA_SIZE} events
- Customers: {CUSTOMERS_COUNT}
""")
