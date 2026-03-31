@echo off
REM ============================================================================
REM TechCorp Customer Success Agent - Database Setup Script
REM ============================================================================
REM This script creates the PostgreSQL user and database in the Docker container.
REM 
REM Prerequisites:
REM   - Docker Desktop must be running
REM   - fte_postgres container must be running
REM   - Docker PostgreSQL must be on port 5433 (to avoid conflict with local PostgreSQL)
REM
REM Usage: database\setup.bat
REM ============================================================================

echo ============================================================
echo TechCorp Customer Success Agent - Database Setup
echo ============================================================
echo.

REM Check if Docker is running
echo [1/5] Checking Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    exit /b 1
)
echo OK: Docker is running
echo.

REM Check if container is running
echo [2/5] Checking fte_postgres container...
docker ps --filter "name=fte_postgres" --format "{{.Names}}" | findstr "fte_postgres" >nul 2>&1
if errorlevel 1 (
    echo WARNING: fte_postgres container is not running
    echo Starting container...
    docker-compose up -d postgres
    timeout /t 5 /nobreak >nul
)
echo OK: fte_postgres container is ready
echo.

REM Create user
echo [3/5] Creating user 'fte_user'...
docker exec fte_postgres psql -U postgres -c "CREATE USER fte_user WITH PASSWORD 'fte_password123';" 2>nul
if errorlevel 1 (
    echo INFO: User may already exist (this is OK)
) else (
    echo OK: User 'fte_user' created
)
echo.

REM Create database
echo [4/5] Creating database 'fte_db'...
docker exec fte_postgres psql -U postgres -c "CREATE DATABASE fte_db OWNER fte_user;" 2>nul
if errorlevel 1 (
    echo INFO: Database may already exist (this is OK)
) else (
    echo OK: Database 'fte_db' created
)
echo.

REM Grant privileges
echo [5/5] Granting privileges...
docker exec fte_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user;" 2>nul
if errorlevel 1 (
    echo WARNING: Could not grant privileges (may already exist)
) else (
    echo OK: Privileges granted
)
echo.

REM Create pgcrypto extension
echo [Bonus] Creating pgcrypto extension...
docker exec fte_postgres psql -U fte_user -d fte_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" 2>nul
if errorlevel 1 (
    echo WARNING: Could not create extension (may already exist)
) else (
    echo OK: Extension created
)
echo.

echo ============================================================
echo User and database created successfully!
echo ============================================================
echo.
echo Database connection details:
echo   Host: localhost:5433
echo   Database: fte_db
echo   User: fte_user
echo   Password: fte_password123
echo.
echo Next steps:
echo   1. Run: python database\apply_schema.py
echo   2. Run: python database\seed_data.py
echo   3. Run: pytest tests\test_database.py -v
echo ============================================================
