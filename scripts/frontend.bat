@echo off
REM Start ONLY the frontend dev server (Windows). Installs deps on first run.
setlocal
cd /d "%~dp0..\frontend"
if not exist "node_modules" (call npm install || exit /b 1)
call npm run dev
endlocal
