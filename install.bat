@echo off
title PhantomTrace Installer
color 0B

echo.
echo  =============================================
echo   PhantomTrace - Setup
echo  =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Download Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo  [1/4] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo  [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo  [3/4] Installing dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo  [4/4] Setting up config...
if not exist "config\.env" (
    copy "config\.env.example" "config\.env" >nul
    echo  [OK] Created config\.env from template.
    echo  [!]  Edit config\.env to add your API keys (optional).
) else (
    echo  [OK] config\.env already exists, skipping.
)

echo.
echo  =============================================
echo   Setup complete!
echo  =============================================
echo.
echo  To run PhantomTrace:
echo    .venv\Scripts\activate
echo    python main.py
echo.
echo  Or just double-click: run.bat
echo.
pause
