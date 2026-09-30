@echo off
title AI Image Matching Engine

echo.
echo 🚀 AI IMAGE MATCHING ENGINE
echo ==============================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    pause
    exit /b 1
)

if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo 🔧 Activating...
call venv\Scripts\activate.bat

echo 📚 Installing dependencies...
pip install -q -r requirements.txt

if not exist ".env" (
    copy .env.example .env
)

echo.
echo ==============================
echo ✅ STARTING APPLICATION
echo ==============================
echo.
echo 🌐 Open browser: http://localhost:8000
echo.
echo Features:
echo   ✅ Upload images with AI vision
echo   ✅ Create blog posts
echo   ✅ Match images to posts
echo   ✅ Guard logic (refuses wrong matches)
echo   ✅ Evaluation metrics
echo.
echo Press Ctrl+C to stop
echo.

python src/main.py

pause
