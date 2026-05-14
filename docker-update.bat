@echo off
REM ##############################################################################
REM # HRM Docker Update Script for Windows
REM # This script automates the process of updating Horilla HRM on Docker
REM # 
REM # Usage: docker-update.bat [option]
REM # Options:
REM #   full      - Full update with rebuild (recommended)
REM #   quick     - Quick update with existing image
REM #   minimal   - Update without stopping containers
REM #   migrate   - Only run database migrations
REM #   logs      - View container logs
REM #   status    - Show container status
REM #   help      - Show this help message
REM ##############################################################################

setlocal enabledelayedexpansion

REM Configuration
set BRANCH=dev-sso-2
set COMPOSE_FILE=docker-compose.yaml

REM Color codes (basic - Windows CMD is limited)
REM Blue = 0B, Green = 0A, Yellow = 0E, Red = 0C

cls

if not exist "%COMPOSE_FILE%" (
    echo [ERROR] docker-compose.yaml not found!
    echo [ERROR] Please run this script from the HRM project root directory
    pause
    exit /b 1
)

REM Parse command line argument
set COMMAND=%1
if "!COMMAND!"=="" set COMMAND=help

if /i "!COMMAND!"=="full" goto full_update
if /i "!COMMAND!"=="quick" goto quick_update
if /i "!COMMAND!"=="minimal" goto minimal_update
if /i "!COMMAND!"=="migrate" goto run_migrations
if /i "!COMMAND!"=="logs" goto view_logs
if /i "!COMMAND!"=="status" goto show_status
if /i "!COMMAND!"=="help" goto show_help

echo [ERROR] Unknown command: !COMMAND!
echo.
goto show_help

:show_status
cls
echo ========================================
echo Container Status
echo ========================================
echo.
docker-compose ps
pause
goto end

:view_logs
cls
echo ========================================
echo Container Logs ^(Press Ctrl+C to exit^)
echo ========================================
echo.
docker-compose logs -f
goto end

:minimal_update
cls
echo ========================================
echo Minimal Update ^(Pull + Restart Container^)
echo ========================================
echo.
echo [INFO] Pulling latest changes from %BRANCH%...
git pull origin %BRANCH%
if errorlevel 1 (
    echo [ERROR] Failed to pull changes
    pause
    exit /b 1
)

echo.
echo [INFO] Restarting web server container...
docker-compose restart server
if errorlevel 1 (
    echo [ERROR] Failed to restart container
    pause
    exit /b 1
)

echo.
echo [INFO] Running database migrations...
docker-compose exec server python manage.py migrate
if errorlevel 1 (
    echo [WARNING] Migration execution had issues, but continuing...
)

echo.
echo [SUCCESS] Minimal update completed!
pause
goto end

:quick_update
cls
echo ========================================
echo Quick Update ^(No Cache Rebuild^)
echo ========================================
echo.
echo [INFO] Pulling latest changes from %BRANCH%...
git pull origin %BRANCH%
if errorlevel 1 (
    echo [ERROR] Failed to pull changes
    pause
    exit /b 1
)

echo.
echo [INFO] Stopping services...
docker-compose down
if errorlevel 1 (
    echo [ERROR] Failed to stop services
    pause
    exit /b 1
)

echo.
echo [INFO] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo.
echo [INFO] Running database migrations...
docker-compose exec server python manage.py migrate
if errorlevel 1 (
    echo [WARNING] Migration execution had issues, but continuing...
)

echo.
echo [INFO] Collecting static files...
docker-compose exec server python manage.py collectstatic --noinput
if errorlevel 1 (
    echo [WARNING] Static file collection had issues, but continuing...
)

echo.
echo [SUCCESS] Quick update completed!
pause
goto end

:full_update
cls
echo ========================================
echo Full Update ^(Recommended^)
echo ========================================
echo.
echo [WARNING] This will rebuild Docker image and restart all services
echo [WARNING] The update may take several minutes
echo.
pause

echo [INFO] Pulling latest changes from %BRANCH%...
git pull origin %BRANCH%
if errorlevel 1 (
    echo [ERROR] Failed to pull changes
    pause
    exit /b 1
)

echo.
echo [INFO] Stopping services...
docker-compose down
if errorlevel 1 (
    echo [ERROR] Failed to stop services
    pause
    exit /b 1
)

echo.
echo [INFO] Building Docker image ^(no cache^)...
echo This may take several minutes...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Failed to build image
    pause
    exit /b 1
)

echo.
echo [INFO] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo.
echo [INFO] Waiting for services to be ready...
timeout /t 5 /nobreak

echo [INFO] Running database migrations...
docker-compose exec server python manage.py migrate
if errorlevel 1 (
    echo [WARNING] Migration execution had issues, but continuing...
)

echo.
echo [INFO] Collecting static files...
docker-compose exec server python manage.py collectstatic --noinput
if errorlevel 1 (
    echo [WARNING] Static file collection had issues, but continuing...
)

echo.
echo [INFO] Creating cache table...
docker-compose exec server python manage.py createcachetable 2>nul
if errorlevel 1 (
    echo [INFO] Cache table already exists or optional
)

echo.
echo [SUCCESS] Full update completed!
pause
goto end

:run_migrations
cls
echo ========================================
echo Running Database Migrations
echo ========================================
echo.
echo [INFO] Running migrations...
docker-compose exec server python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Migration failed
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Migrations completed!
pause
goto end

:show_help
cls
echo.
echo ========================================
echo      HRM Docker Update Script
echo ========================================
echo.
echo USAGE:
echo   docker-update.bat [option]
echo.
echo OPTIONS:
echo   full      - Full update with rebuild ^(recommended for production^)
echo   quick     - Quick update with existing image ^(faster^)
echo   minimal   - Update without stopping containers ^(for minor changes^)
echo   migrate   - Only run database migrations
echo   logs      - View container logs
echo   status    - Show container status
echo   help      - Show this help message
echo.
echo EXAMPLES:
echo   docker-update.bat full      # Full rebuild and start
echo   docker-update.bat quick     # Quick restart with new code
echo   docker-update.bat logs      # View live logs
echo   docker-update.bat status    # Check service status
echo.
echo NOTES:
echo   - Ensure you are in the HRM project directory
echo   - Docker Desktop must be installed and running
echo   - Backup your database before running full update
echo   - Configure .env with Microsoft credentials if using SSO
echo.
pause
goto end

:end
endlocal
