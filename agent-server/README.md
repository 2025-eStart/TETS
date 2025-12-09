# 실행 방법

터미널에서 아래 명령어들을 수행한다.

1. 가상환경 생성 및 실행
    > `.venv`라는 이름의 가상환경을 만들고 터미널에서 `source .venv/bin/activate` 실행
2. 의존성 설치: `pip install -e requirements.txt` 또는 ``
3. `uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload` 실행
