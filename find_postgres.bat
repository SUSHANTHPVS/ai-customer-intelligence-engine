@echo off
REM Find PostgreSQL installation

echo Finding PostgreSQL Installation... > C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt

if exist "C:\Program Files\PostgreSQL" (
    echo Found in C:\Program Files\PostgreSQL >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
    dir "C:\Program Files\PostgreSQL" >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
) else (
    echo Not found in C:\Program Files\PostgreSQL >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
)

if exist "C:\Program Files (x86)\PostgreSQL" (
    echo Found in C:\Program Files (x86)\PostgreSQL >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
    dir "C:\Program Files (x86)\PostgreSQL" >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
) else (
    echo Not found in C:\Program Files (x86)\PostgreSQL >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
)

REM Check Windows services
echo. >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
echo PostgreSQL Services: >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt
sc query | find "postgres" >> C:\Users\SUSHANTH\Desktop\AI_Customer_Intelligence_Engine\postgres_location.txt

echo Done. Check postgres_location.txt
