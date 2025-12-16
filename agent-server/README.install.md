# 설치 및 실행 가이드 (Installation Guide)

본 문서는 '챗봇 Lucie'의 백엔드 서버인 Agent Server의 설치 및 실행 방법을 설명합니다.

## 1. 사전 요구 사항 (Prerequisites)
* **OS:** Windows 10/11, macOS, Linux 지원
* **프로그래밍 언어:** Python 3.10 이상 (3.11 권장)
    * *확인 방법: 터미널에 `python --version` 입력*
* **네트워크:** 외부 API(OpenAI, Pinecone, Firebase) 호출을 위한 인터넷 연결 필수
* **필수 API 키:** (메일로 제출된 키(채점자) 또는 스스로 발급받은 키)
    * OpenAI API Key: 메일에 키 첨부; .env에 저장
    * Pinecone API Key: 메일에 키 첨부; .env에 저장
    * Firebase/Google Cloud Credentials: 메일 첨부파일(`.firease_key.json`)

## 2. 필수 파일 준비
### 2-1. `.env` 준비
`agent-server/.env.template`에 필요한 변수가 준비되어 있습니다.

1. 이 파일에서 아래 부분을 찾아, 각 키의 값을 붙여넣어 주세요.
    ```
    # ======== API 키 설정 ========
    OPENAI_API_KEY=
    PINECONE_API_KEY=
    LANGSMITH_API_KEY=
    ```
2. `.env.template` 파일 이름을 `.env`로 변경하여 환경변수 파일(`.env`)로 만들어주세요.

### 2-2. `.firebase_key.json` 준비
메일에 첨부된 `.firebase_key.json` 파일을 서버 프로젝트 루트(`agent-server/`)에 저장해 주세요.

## 3. 원클릭 설치 및 실행
프로젝트 폴더(`agnet-server/`)에 포함된 자동화 스크립트를 사용하면 가상환경 생성부터 실행까지 한 번에 진행됩니다.

* **Windows 사용자:**
  `install_and_run.bat` 파일을 더블 클릭하세요.

* **Mac/Linux 사용자:**
  터미널에서 아래 명령어를 입력하세요.
  ```bash
  chmod +x install_and_run.sh
  ./install_and_run.sh

## 4. 수동 설치 방법 (Manual Installation)
스크립트 실행이 안 될 경우 아래 순서대로 진행하세요.

1. 가상환경 생성(`agent-server` 위치에서): python -m venv .venv
2. 가상환경 활성화: source .venv/bin/activate (Windows: .venv\Scripts\activate)
3. 패키지 설치: pip install -r requirements.txt
4. 서버 실행: uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload