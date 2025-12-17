# Build & Installation Guide

## 1. Prerequisites

프로젝트를 로컬 환경에서 실행(Build/Install)하기 위해 다음 준비가 필요합니다.

### 1.1. Backend Requirements

* **OS:** Windows 10/11, macOS, Linux
* **Python:** 3.10 이상 (3.11 권장)
* **Essential Keys (.env):** 보안을 위해 제외되었습니다. **메일로 별도 제출된 환경 변수 파일**이 필요합니다.
  * `.env` (OpenAI, Pinecone API Key 포함)
  * `.firebase_key.json` (Google Service Account Key)

### 1.2. Frontend Requirements

* **Device:** Android 스마트폰 또는 Android Studio Emulator (API Level 26+)
* **Network:** 외부 API 호출을 위한 인터넷 연결 필수

---

## 🛠️ 2. How to Build & Install

### 2.1. Backend Server (agent-server)

서버를 로컬에서 구동하는 방법입니다.
상세 내용은 [android-app의 README.install](agent-server/README.install.md)를 참고해주세요.

**1. 환경 설정 파일 준비**

1. 메일로 받으신 `.firebase_key.json` 파일을 `agent-server/` 폴더 최상위에 넣어주세요.
2. 메일로 받으신 API 키를 `.env.template` 파일의 적절한 변수에 입력하고 파일명을 수정하여 `.env` 파일을 만들어주세요.

**2. 자동 설치 및 실행 (Recommended)**
폴더 내의 자동화 스크립트를 사용하면 가상환경 생성, 패키지 설치, 서버 실행이 한 번에 완료됩니다.

* **Windows:** `agent-server/install_and_run.bat` 더블 클릭
* **Mac/Linux:** 터미널에서 `chmod +x install_and_run.sh` 후 `./install_and_run.sh` 실행

**3. 수동 설치 (Manual)**
스크립트 실행이 불가능한 경우 아래 명령어를 순서대로 입력하세요.

```bash
cd agent-server
python -m venv .venv                  # 가상환경 생성
source .venv/bin/activate             # 가상환경 활성화 (Win: .venv\Scripts\activate)
pip install -r requirements.txt       # 의존성 설치
pip install -e .                      # 내 폴더의 프로젝트를 등록
uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload  # 서버 실행
```

### 2.2. Android Client (android-app)

상세 내용은 [android-app의 README.install](android-app/README.install.md) 참고

#### Option 1. 시제품 APK 바로 실행

소스 코드 빌드 없이 즉시 테스트할 수 있습니다. 별도로 제출된 시제품 apk 파일을 실행합니다.

* 설치법: 파일을 Android 기기/에뮬레이터에 넣어 설치합니다.
* 서버 연결: 이 APK는 **이미 배포된 테스트 서버(AWS EC2)**와 연결되어 있어, 로컬 서버를 켜지 않아도 작동합니다.

#### Option 2. 소스 코드 빌드 및 로컬 서버 연결

배포된 서버가 실행되지 않거나, 로컬 서버(localhost)와 통신 과정을 확인하고 싶은 경우 직접 빌드합니다.

1. Android Studio에서 android-app 폴더를 엽니다.
2. `android-app/app/build.gradle.kts` 파일에서 `buildConfigField()`의 주소를 수정합니다.
  * `buildConfigField("String", "API_BASE_URL", "\"http://54.180.125.238:8000/\"")`를 주석처리하거나 `http://54.180.125.238` 주소를 실제 사용할 기기의 주소로 변경합니다.
  * 애뮬레이터를 이용하는 경우, `buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8123/\"")`를 이용하면 됩니다.

```Kotlin
// 로컬 호스트 사용 시: 애뮬레이터용 주소
// 애뮬레이터가 아닌 실제 기기를 이용할 시 `http://10.0.2.2`를 실제 기기의 주소로 변경해야 합니다.
// buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8123/\"")

// EC2 public IP 주소 + 포트 8000 (로컬 호스트 사용 시 주석 처리)
buildConfigField("String", "API_BASE_URL", "\"http://54.180.125.238:8000/\"")

```

3. 상단의 Run (▶) 버튼을 눌러 빌드 및 설치를 진행합니다.

---

## 3. How to Test

### 3.1. Authentication (계정 정보)

본 서비스는 사용자의 접근성을 위해 **별도의 회원가입 절차 없이** 기기 고유 ID를 이용한 **자동 로그인(Anonymous Login)** 방식을 사용합니다.

* **No Account Required:** 별도의 아이디/비밀번호 입력이 필요 없습니다.
* **Auto Login:** 앱 실행 시 자동으로 세션이 생성되며 즉시 서비스를 이용할 수 있습니다.

### 3.2. Verification Steps (작동 확인 절차)

설치가 완료된 후, 다음 순서대로 시제품의 정상 작동 여부를 확인하실 수 있습니다.

**Step 1. 앱 실행 및 접속**

  * 앱 아이콘을 클릭하여 실행합니다.
  * 별도의 로그인 화면 없이 메인 채팅 화면(또는 초기 설정 화면)으로 진입하면 **정상**입니다.

**Step 2. 서버 연결 확인**

* 앱 진입 시 바로 상담 내용이 생성됩니다. 상담 내용이 생성되는 동안 '루시가 여행자님의 말을 곰곰이 생각중이에요'와 같은 로딩 문구가 출력됩니다. 응답 생성 소요 시간은 2분 미만입니다.
  * 첫 사용자라면 'WEEKLY' 상담이 실행됩니다. 로딩 이후 상단 바에 "상담" 문구가 뜨고, 챗봇의 응답이 출력되면 정상적으로 연결된 것입니다.
  * WEEKLY 상담을 이미 수행한 사용자라면 앱에 접속했을 때 일반 FAQ 상담이 진행됩니다. 진입 시 바로 일반 상담 안내 문구가 출력됩니다.
* 챗봇의 응답이 나타나면, 그 응답을 보고 채팅창에 적절한 답변을 입력합니다.
* **[성공 기준]**
  * 채팅 전송 아이콘이 로딩 아이콘으로 바뀌고, 채팅 화면에 챗봇이 응답을 생성 중임을 안내하는 문구가 뜹니다.
  * 2분 내에 챗봇으로부터 답변이 도착합니다.
* **[참고]:** 답변이 온다면 백엔드 서버(LangGraph) 및 외부 API(OpenAI, Pinecone)가 모두 정상적으로 연결된 상태입니다.

**Step 3. (선택) 로컬 서버 로그 확인**

* 로컬 서버를 구동 중이라면, 터미널에서 디버깅을 위한 출력문을 통해 오류 지점을 확인할 수 있습니다.

---