@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo Cross-Border Blockchain Payment Demo
echo ===============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.9 or newer and try again.
  pause
  exit /b 1
)
if not exist "venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv venv
  if errorlevel 1 (
    echo Could not create virtual environment.
    pause
    exit /b 1
  )
)
echo Installing/checking required package...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Check your internet connection.
  pause
  exit /b 1
)
echo Starting app. Keep this window open while using the demo.
"venv\Scripts\python.exe" -m streamlit run app.py
pause
