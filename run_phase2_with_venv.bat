@echo off
REM Activate venv and run Phase 2 setup
cd /d "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the setup script
echo postgres | python phase2_setup.py > phase2_setup_output.log 2>&1

REM Log completion
echo Setup completed at %date% %time% >> phase2_setup_output.log

REM Keep window open for 10 seconds to see results
timeout /t 10
