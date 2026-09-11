@echo off
REM Test PostgreSQL connection
setlocal enabledelayedexpansion

echo Testing PostgreSQL connection...
echo.

REM Try to connect using psql
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -c "SELECT version();" > postgres_test_output.txt 2>&1

echo.
echo Connection test completed. Output:
type postgres_test_output.txt

pause
