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
    echo "Please create a '.env' file in this folder using"
    echo "the keys provided via email."
    echo "---------------------------------------------------"
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

# 5. 서버 실행
echo ""
echo "[Start] Launching FastAPI Server..."
uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload