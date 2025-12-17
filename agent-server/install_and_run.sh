#!/bin/bash

# 스크립트 위치로 이동
cd "$(dirname "$0")"

echo "==================================================="
echo "  [Agent Server] Auto Installer & Launcher"
echo "==================================================="

# 1. .env 파일 확인
if [ ! -f ".env" ]; then
    echo ""
    echo "[ERROR] .env file not found!"
    echo "---------------------------------------------------"
    echo "❗️ .env 파일이 존재하지 않습니다.❗️"
    echo "메일로 보내드린 키를 이용해 .env.template을 수정하고"
    echo ".env로 해당 파일명을 수정해주세요."
    echo "---------------------------------------------------"
    echo ""
    exit 1
fi
if [ ! -f ".firebase_key.json" ]; then
    echo ""
    echo "[ERROR] .firebase_key.json file not found!"
    echo "----------------------------------------------------------"
    echo "❗️ .firebase_key.json 파일이 존재하지 않습니다.❗️"
    echo "메일로 보내드린 .firebase_key.template.json을"
    echo "실행 파일(install_and_run.bat)과 동일한 위치에 복사한 후 저장해주세요."
    echo "❗️ 파일명은 반드시 .firebase_key.json 이어야 합니다."
    echo "----------------------------------------------------------"
    echo ""
    exit 1
fi

# 2. 가상환경 생성
if [ ! -d ".venv" ]; then
    echo "[Setup] Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. 가상환경 활성화
source .venv/bin/activate

# 4. 라이브러리 설치
echo "[Setup] Checking/Installing dependencies..."
pip install -r requirements.txt
echo "[Setup] Installing current project in editable mode..."
pip install -e .

# 5. 서버 실행
echo ""
echo "[Start] Launching FastAPI Server..."
uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload