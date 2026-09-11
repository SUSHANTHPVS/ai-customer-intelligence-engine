@echo off
REM Phase 2 PostgreSQL Setup Batch File
setlocal enabledelayedexpansion

cd /d "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

echo.
echo ================================================================
echo Phase 2: PostgreSQL Database Setup
echo ================================================================
echo.
echo Starting setup... Output will be saved to phase2_setup_output.log
echo.

REM Run Python script with password input and save output
echo postgres | python phase2_setup.py > phase2_setup_output.log 2>&1

echo.
echo Setup completed. Output saved to: phase2_setup_output.log
echo.
echo View results with: type phase2_setup_output.log
echo.
pause
