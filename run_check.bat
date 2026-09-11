@echo off
cd /d "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

REM Try to run Python check and capture output
REM Use venv Python directly
call venv\Scripts\activate.bat

REM Run the check script
python direct_postgres_check.py 2>&1 > temp_check_output.txt

REM Display the output
type temp_check_output.txt

REM Also list what files were created
echo.
echo Files created:
dir *.json 2>nul
dir *.log 2>nul
dir *.txt 2>nul

pause
