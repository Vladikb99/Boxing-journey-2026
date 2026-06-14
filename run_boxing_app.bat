@echo off
title Boxing Journey 2026

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Could not find .venv\Scripts\python.exe
    echo.
    echo Open PowerShell in this folder and run:
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting Boxing Journey 2026...
echo.

".venv\Scripts\python.exe" -m streamlit run app.py

pause