@echo off
REM Phase 5 API Server Startup Script (Windows)
REM Usage: run_phase5.bat

setlocal enabledelayedexpansion

cls
echo ========================================================================
echo PHASE 5: ML MODEL PREDICTION API SERVER
echo ========================================================================
echo.

REM Colors (Windows doesn't support ANSI by default, using text only)
set GREEN=[OK]
set RED=[ERROR]
set YELLOW=[INFO]

REM Step 1: Check Python
echo %YELLOW% [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED% Python not found. Please install Python 3.14+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN% Python !PYTHON_VERSION! found

REM Step 2: Check dependencies
echo.
echo %YELLOW% [2/5] Checking dependencies...
python -c "import flask, psycopg2, pandas, numpy, sklearn" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW% Installing missing dependencies...
    pip install -q -r requirements-phase5.txt
    echo %GREEN% Dependencies installed
) else (
    echo %GREEN% All dependencies present
)

REM Step 3: Check model files
echo.
echo %YELLOW% [3/5] Verifying model files...
set MISSING_FILES=0
set REQUIRED_FILES=^
    models\churn_model.pkl^
    models\churn_scaler.pkl^
    models\engagement_model.pkl^
    models\engagement_scaler.pkl^
    models\revenue_model.pkl^
    models\revenue_scaler.pkl^
    models\segmentation_model.pkl^
    models\segmentation_scaler.pkl

for %%f in (%REQUIRED_FILES%) do (
    if not exist "%%f" (
        echo %RED% Missing: %%f
        set /a MISSING_FILES=!MISSING_FILES!+1
    )
)

if !MISSING_FILES! equ 0 (
    echo %GREEN% All model files present (8/8)
) else (
    echo %RED% !MISSING_FILES! model files missing
    echo %YELLOW% Please run Phase 4 first: python phase4_setup.py
    pause
    exit /b 1
)

REM Step 4: Database connectivity check
echo.
echo %YELLOW% [4/5] Checking database connectivity...
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, database='customer_intelligence', user='postgres', password='sushanth123'); conn.close(); print('OK')" >nul 2>&1
if errorlevel 1 (
    echo %RED% Database connection failed
    echo %YELLOW% Make sure PostgreSQL is running and configured
    pause
    exit /b 1
) else (
    echo %GREEN% Database connectivity verified
)

REM Step 5: Start API server
echo.
echo %YELLOW% [5/5] Starting API server...
echo.
echo ========================================================================
echo API Server Starting...
echo ========================================================================
echo.

REM Set PostgreSQL password for database operations
set PGPASSWORD=sushanth123

REM Start Python API server
python phase5_api_server.py

pause
