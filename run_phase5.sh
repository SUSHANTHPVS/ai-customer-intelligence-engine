#!/usr/bin/env bash
# Phase 5 API Server Startup Script
# ====================================
# Usage: bash run_phase5.sh

set -e

echo "========================================================================"
echo "PHASE 5: ML MODEL PREDICTION API SERVER"
echo "========================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}[1/5] Checking Python installation...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found. Please install Python 3.14+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Step 2: Check dependencies
echo ""
echo -e "${YELLOW}[2/5] Checking dependencies...${NC}"
if ! python -c "import flask, psycopg2, pandas, numpy, sklearn" 2>/dev/null; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install -q -r requirements-phase5.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ All dependencies present${NC}"
fi

# Step 3: Check model files
echo ""
echo -e "${YELLOW}[3/5] Verifying model files...${NC}"
REQUIRED_MODELS=(
    "models/churn_model.pkl"
    "models/churn_scaler.pkl"
    "models/engagement_model.pkl"
    "models/engagement_scaler.pkl"
    "models/revenue_model.pkl"
    "models/revenue_scaler.pkl"
    "models/segmentation_model.pkl"
    "models/segmentation_scaler.pkl"
)

MISSING_FILES=0
for file in "${REQUIRED_MODELS[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    echo -e "${GREEN}✓ All model files present (8/8)${NC}"
else
    echo -e "${RED}✗ ${MISSING_FILES} model files missing${NC}"
    echo -e "${YELLOW}Please run Phase 4 first: python phase4_setup.py${NC}"
    exit 1
fi

# Step 4: Database connectivity check
echo ""
echo -e "${YELLOW}[4/5] Checking database connectivity...${NC}"
if python -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='customer_intelligence',
        user='postgres',
        password='sushanth123'
    )
    conn.close()
    print('✓ Database connected')
except Exception as e:
    print(f'✗ Database error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connectivity verified${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo -e "${YELLOW}Make sure PostgreSQL is running and configured${NC}"
    exit 1
fi

# Step 5: Start API server
echo ""
echo -e "${YELLOW}[5/5] Starting API server...${NC}"
echo ""
echo -e "${GREEN}=======================================================================${NC}"
echo -e "${GREEN}API Server Starting...${NC}"
echo -e "${GREEN}=======================================================================${NC}"
echo ""

python phase5_api_server.py
