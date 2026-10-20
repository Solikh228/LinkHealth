@echo off
set TARGET=%1
if "%TARGET%"=="" set TARGET=help

if "%TARGET%"=="run" goto run
if "%TARGET%"=="backend" goto backend
if "%TARGET%"=="frontend" goto frontend
if "%TARGET%"=="dev" goto dev
if "%TARGET%"=="test" goto test
if "%TARGET%"=="test-backend" goto test_backend
if "%TARGET%"=="test-frontend" goto test_frontend
if "%TARGET%"=="install" goto install
if "%TARGET%"=="build" goto build
if "%TARGET%"=="openapi" goto openapi
if "%TARGET%"=="help" goto help

echo Unknown target: %TARGET%
echo Run 'make help' for available targets.
exit /b 1

:run
cd backend && uv run uvicorn backend.main:app --reload --port 8091
goto end

:backend
cd backend && uv run uvicorn backend.main:app --reload --port 8091
goto end

:frontend
cd frontend && npm.cmd run dev
goto end

:dev
echo Starting backend on port 8091 and frontend on port 5173...
start cmd /k "cd backend && uv run uvicorn backend.main:app --reload --port 8091"
cd frontend && npm.cmd run dev
goto end

:test
call :test_backend
call :test_frontend
goto end

:test_backend
echo Running backend tests...
cd /d "%~dp0backend" && uv run pytest
cd /d "%~dp0"
goto end

:test_frontend
echo Running frontend tests...
cd /d "%~dp0frontend" && npm.cmd test -- --run
cd /d "%~dp0"
goto end

:install
echo Installing backend dependencies...
cd /d "%~dp0backend" && uv sync
echo Installing frontend dependencies...
cd /d "%~dp0frontend" && npm.cmd install
cd /d "%~dp0"
goto end

:build
cd /d "%~dp0frontend" && npm.cmd run build
cd /d "%~dp0"
goto end

:openapi
cd /d "%~dp0backend" && uv run python scripts/export_openapi.py
cd /d "%~dp0"
goto end

:help
echo Available targets:
echo   make run           - Run the backend server on port 8091
echo   make dev           - Run both backend and frontend
echo   make backend       - Run backend server on port 8091
echo   make frontend      - Run frontend Vite server on port 5173
echo   make test          - Run all tests (backend and frontend)
echo   make test-backend  - Run backend pytest suite
echo   make test-frontend - Run frontend vitest suite
echo   make install       - Install all dependencies
echo   make build         - Build frontend for production
echo   make openapi       - Re-export openapi.yaml specification
goto end

:end
