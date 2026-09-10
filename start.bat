@echo off
REM BorderGuard AI - one-command local startup for Windows 10/11.
REM Creates the backend venv (if missing), installs deps, then opens the
REM backend (:8000) and frontend (:5173) in separate windows.
REM
REM First run needs internet (pip + npm). For an OFFLINE demo, run once online,
REM then also run:  cd backend ^&^& .venv\Scripts\activate ^&^& python -m app.preload
setlocal
cd /d "%~dp0"

echo ==^> BorderGuard AI starting...

where py >nul 2>nul && (set "PY=py -3.11") || (set "PY=python")

%PY% --version >nul 2>nul || (echo ERROR: Python not found. Install Python 3.11 and check "Add to PATH". & exit /b 1)
where node >nul 2>nul || (echo ERROR: node not found. Install Node.js LTS. & exit /b 1)

REM --- Backend ---
if not exist "backend\.venv" (
  echo ==^> Creating backend virtual environment...
  %PY% -m venv backend\.venv
)
call backend\.venv\Scripts\activate.bat
echo ==^> Installing backend dependencies...
python -m pip install --upgrade pip >nul
pip install -r backend\requirements.txt || (echo ERROR: backend dependency install failed. & exit /b 1)

REM --- Frontend ---
if not exist "frontend\node_modules" (
  echo ==^> Installing frontend dependencies...
  pushd frontend
  call npm install || (echo ERROR: npm install failed. & popd & exit /b 1)
  popd
)

REM --- Run both (separate windows) ---
echo ==^> Launching backend (:8000) and frontend (:5173) in new windows...
start "BorderGuard Backend" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && uvicorn app.main:app --port 8000"
start "BorderGuard Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000/api/health
echo Frontend: http://localhost:5173
echo Close the two opened windows to stop the servers.
endlocal
