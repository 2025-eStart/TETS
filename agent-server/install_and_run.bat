@echo off
cd /d "%~dp0"

echo ===================================================
echo   [Agent Server] Auto Installer & Launcher
echo ===================================================

:: 1. .env 파일 존재 여부, 위치 확인 및 이동
if exist .env (
    echo [System] Copying .env file to server core...
    copy /Y .env server_core\.env >nul
)
cd source_code

if not exist .env (
    echo.
    echo [ERROR] .env file not found!
    echo ---------------------------------------------------------
    echo ❗️ .env 파일이 존재하지 않습니다.❗️
    echo 메일로 보내드린 키를 이용해 .env.template을 수정하고
    echo .env로 해당 파일명을 수정해주세요.
    echo ---------------------------------------------------------
    echo.
    pause
    exit
)
if not exist .firebase_key.json (
    echo.
    echo [ERROR] .firebase_key.json file not found!
    echo ----------------------------------------------------------
    echo ❗️ .firebase_key.json 파일이 존재하지 않습니다.❗️
    echo 메일로 보내드린 .firebase_key.template.json을
    echo 실행 파일(install_and_run.bat)과 동일한 위치에 복사한 후 저장해주세요.
    echo ❗️ 파일명은 반드시 .firebase_key.json 이어야 합니다.
    echo ----------------------------------------------------------
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