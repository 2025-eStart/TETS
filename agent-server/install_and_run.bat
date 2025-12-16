@echo off
cd /d "%~dp0"

echo ===================================================
echo   [Agent Server] Auto Installer & Launcher
echo ===================================================

:: 1. .env 파일 존재 여부 확인
if not exist .env (
    echo.
    echo [ERROR] .env file not found!
    echo ---------------------------------------------------
    echo Please create a '.env' file in this folder using
    echo the keys provided via email.
    echo ---------------------------------------------------
    echo.
    pause
    exit
)

:: 2. 가상환경(.venv)이 없으면 생성
if not exist .venv (
    echo [Setup] Creating virtual environment...
    python -m venv .venv
)

:: 3. 가상환경 활성화
call .venv\Scripts\activate

:: 4. 라이브러리 자동 설치 (새로운게 있을 때만 설치됨)
echo [Setup] Checking/Installing dependencies...
pip install -r requirements.txt

:: 5. 서버 실행
echo.
echo [Start] Launching FastAPI Server...
echo Access the server at: http://localhost:8000
echo.
:: 실제 실행 명령어
uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload

pause