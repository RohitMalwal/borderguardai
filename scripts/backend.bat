@echo off
REM Start ONLY the backend (Windows). Creates venv + installs on first run.
setlocal
cd /d "%~dp0.."
where py >nul 2>nul && (set "PY=py -3.11") || (set "PY=python")
if not exist "backend\.venv" %PY% -m venv backend\.venv
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r backend\requirements.txt || exit /b 1
cd backend
uvicorn app.main:app --reload --port 8000
endlocal
