# 이화여자대학교 2025 spring capstone design project – [소비 코치 Lucie]

본 레포지토리는  이화여자대학교 컴퓨터공학과 2025년 spring(스타트)-autumn(그로쓰) 캡스톤 디자인 프로젝트로 진행한 **28-e스타트**팀 **[소비 코치 Lucie]**의 소스코드와 자료를 정리한 공간입니다.

## 1. 팀 & 과제 소개

### 1.1. 과제명

**ChatGPT API와 RAG, 인지행동치료 기반 상담형 챗봇을 통한, 20대 여성 대상 충동 소비 습관 교정 코칭 서비스**

### 1.2. 팀명 & 팀원

28-e스타트

* 유희정: leader, FE, BE
* 최윤우: DB 테스트
* 이경림: 자료 제출

### 1.3. 과제 키워드

챗봇, RAG, ChatGPT API, 충동 소비(Impulse Buying) CBT(Cognitive Behavioral Therapy)

### 1.4. 프로젝트 개요

본 프로젝트는 20대 여성의 충동 소비 습관을 교정하기 위한 CBT(인지행동치료) 기반 상담형 코칭 앱입니다.
Mitchell et al.(2006)1과 Leite et al.(2014)2의 연구를 참고한 10주차 CBT 프로토콜을 바탕으로, LangGraph를 통해 실제 상담 과정을 대화형 챗봇으로 구현했습니다. 앱은 세 가지 세션으로 구성됩니다.

1. 주간 상담 세션: 각 주차별 CBT 주제(예: Psycho-education, Money Management, Cognitive Restructuring 등)에 따라 사용자의 소비 경험을 탐색하고, 감정·사고·행동 패턴을 재구조화하며 과제를 제시합니다.
2. 일일 체크 세션: 주간 상담에서 제시된 과제의 수행을 돕고, 일상 속 소비 충동과 대처 전략 적용 여부를 짧게 점검합니다.
3. 일반 FAQ 세션: 소비습관 관련 질문에 대해 RAG 기반 근거 응답을 제공합니다.
RAG에는 인지행동치료의 개념, 충동소비와 강박적소비장애의 연관성, 강박적소비장애에 대한 인지행동치료와 그 사례에 대한 논문, 주차별 상담 지침이 포함되어 있습니다.
이 서비스를 통해 사용자는 충동소비의 심리적 원인을 이해하고, 스스로의 소비 패턴을 점진적으로 교정할 수 있습니다.

**[참고논문]**

1. Mitchell, J. E., Burgard, M., Faber, R., Crosby, R. D., & de Zwaan, M. (2006). Cognitive behavioral therapy for compulsive buying disorder. Behaviour Research and Therapy, 44(12), 1859-1865. https://doi.org/10.1016/j.brat.2005.12.009
2. Leite, P. L., Pereira, V. M., Nardi, A. E., & Silva, A. C. (2014). Psychotherapy for compulsive buying disorder: A systematic review. Psychiatry Research, 219(3), 411-419. https://doi.org/10.1016/j.psychres.2014.05.037

---

## 2. Source Code Description

### 2.1. Backend Server (`agent-server/`)

* **LangGraph & LangChain:** 상담 챗봇 워크플로우(Supervisor, Weekly, General) 및 상태 관리
* **FastAPI:** 비동기 웹 서버 및 API 엔드포인트 제공
* **RAG Pipeline:** Pinecone Vector DB를 활용한 상담 프로토콜 검색
* **Firestore Integration:** 대화 내역 및 사용자 상태 영구 저장

### 2.2. Android Client (`android-app/`)

* **Kotlin & Jetpack Compose:** 안드로이드 채팅 인터페이스
* **Retrofit2:** 백엔드 서버와의 통신 모듈

### 🗂️ 레포지토리 구성

<pre>
Lucie/
├─ README.md
├─ .gitignore
├─ Makefile                         # 서버/앱 빌드·실행 단축
├─ agent-server/
│   ├─ src/
│     │  ├─ coach_agent/
│     │  │  ├─ graph/
│     │  │  ├─ prompts/
│     │  │  ├─ protocols/
│     │  │  ├─ rag/
│     │  │  ├─ services/
│     │  │  ├─ utils/
│     │  │  ├─ agent.py
│     │  │  ├─ settings.py
│     │  │  ├─ configuration.py
│     │  │  ├─ prompts.py
│     │  │  └─ state_types.py
│     │  └─ main.py
│     ├─ requirements.txt
│     ├─ test_db.py
│     ├─ .env.template               # 환경변수 템플릿
│     ├─ 
│     │  ├─ .env                    # (gitignored)
│     │  └─ .firebase_key.json       # (gitignored)
│     └─ .gitignore                 # 서버 전용 ignore
└─ android/
   └─ impulsecoachapp/
      ├─ app/
      │  ├─ manifests/
      │  ├─ kotlin+java/
      │  └─ res/
      ├─ build.gradle.kts (Project)
      ├─ build.gradle.kts (Module:app)
      ├─ lib.version.toml
      ├─ gradle/
      ├─ gradlew / gradlew.bat
      └─ settings.gradle.kts

</pre>

---

## 3. Prerequisites

프로젝트를 로컬 환경에서 실행(Build/Install)하기 위해 다음 준비가 필요합니다.

### 3.1. Backend Requirements

* **OS:** Windows 10/11, macOS, Linux
* **Python:** 3.10 이상 (3.11 권장)
* **Essential Keys (.env):** 보안을 위해 제외되었습니다. **메일로 별도 제출된 환경 변수 파일**이 필요합니다.
  * `.env` (OpenAI, Pinecone API Key 포함)
  * `.firebase_key.json` (Google Service Account Key)

### 3.2. Frontend Requirements

* **Device:** Android 스마트폰 또는 Android Studio Emulator (API Level 26+)
* **Network:** 외부 API 호출을 위한 인터넷 연결 필수

---

## 🛠️ 4. How to Build & Install

### 4.1. Backend Server (agent-server)

서버를 로컬에서 구동하는 방법입니다.

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
uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload  # 서버 실행
```

### 4.2. Android Client (android-app)

앱을 설치하고 실행하는 두 가지 방법입니다.

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

## 5. How to Test

### 5.1. Authentication (계정 정보)

본 서비스는 사용자의 접근성을 위해 **별도의 회원가입 절차 없이** 기기 고유 ID를 이용한 **자동 로그인(Anonymous Login)** 방식을 사용합니다.

* **No Account Required:** 별도의 아이디/비밀번호 입력이 필요 없습니다.
* **Auto Login:** 앱 실행 시 자동으로 세션이 생성되며 즉시 서비스를 이용할 수 있습니다.

### 5.2. Verification Steps (작동 확인 절차)

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

## 6. Data & Open Source Info

### 6.1. Data 

### 6.1. Knowledge Base (RAG Data)
본 서비스의 코칭 에이전트는 전문적인 심리 상담을 수행하기 위해, 검증된 학술 논문과 상담 프로토콜을 기반으로 지식 베이스(Knowledge Base)를 구축하였습니다.

* **Data Processing:**
  * 참고 문헌의 핵심 상담 기법을 구조화된 **YAML 프로토콜**로 변환 (`src/coach_agent/protocols/`)
  * **Pinecone Vector DB**에 임베딩하여 RAG(Retrieval-Augmented Generation) 시스템에 활용
  * 사용자의 상황에 맞는 논문 기반의 근거 있는 조언(Evidence-based Advice) 제공

### 6.2. Key References (참고 문헌)
RAG 임베딩 및 상담 로직 설계에 참고한 주요 논문은 다음과 같습니다.
상담 프로토콜 파일(`agent-server/src/coach_agent/protocols/v2/week{n}.yaml`) 및 기법 파일(`agent-server/src/coach_agent/protocols/v2/techniques.yaml`)에 대한 내용은 `agent-server/.../protocols/`내의 `README` 파일을 참고해주세요.

1. Beck, J. S. (2011). Cognitive behavior therapy: Basics and beyond (2nd ed.). Guilford Press. (p. 2)
2. Black, D. W. (2007). A review of compulsive buying disorder. World Psychiatry, 6(1), 14–18. https://doi.org/10.1002/j.2051-5545.2007.tb00132.x
3. Darrat, A. A., Darrat, M. A., & Amyx, D. (2016). How impulse buying influences compulsive buying: The central role of consumer anxiety and escapism. Journal of Retailing and Consumer Services, 31, 103–108. https://doi.org/10.1016/j.jretconser.2016.03.009
4.Leite, P. L., Pereira, V. M., Nardi, A. E., & Silva, A. C. (2014). Psychotherapy for compulsive buying disorder: A systematic review. Psychiatry Research, 219(3), 411–419. https://doi.org/10.1016/j.psychres.2014.06.013
5. Lejoyeux, M., Adès, J., Tassain, V., & Solomon, J. (1997). Phenomenology and psychopathology of uncontrolled buying. American Journal of Psychiatry, 154(2), 263–267. https://doi.org/10.1176/ajp.154.2.263
6. Miltenberger, R. G., Redlin, J., Crosby, R., Stickney, M., Mitchell, J., Wonderlich, S., & Smyth, J. (1995). Direct and retrospective assessment of factors contributing to compulsive buying. Journal of Behavior Therapy and Experimental Psychiatry, 26(3), 291–300. [https://doi.org/10.1016/0005-7916(95)00017-8](https://doi.org/10.1016/0005-7916(95)00017-8)
7. Mitchell, J. E., Burgard, M., Faber, R., Crosby, R. D., & de Zwaan, M. (2006). Cognitive behavioral therapy for compulsive buying disorder. Behaviour Research and Therapy, 44(12), 1859–1865. https://doi.org/10.1016/j.brat.2006.01.010
8. Müller, A., Mitchell, J. E., Crosby, R. D., Cao, L., Johnson, J., Claes, L., de Zwaan, M. (2013). Estimated prevalence of compulsive buying in Germany and its association with sociodemographic characteristics and depressive symptoms. Psychiatry Research, 210(3), 857–862. https://doi.org/10.1016/j.psychres.2013.08.018
9. Rodrigues, R. I., Lopes, P., & Varela, M. (2021). Factors affecting impulse buying behavior of consumers. Frontiers in Psychology, 12, 697080. https://doi.org/10.3389/fpsyg.2021.697080
10. Tavares, H., Lobo, D. S. S., Fuentes, D., & Black, D. W. (2008). Compulsive buying disorder: A review and a case vignette. Revista Brasileira de Psiquiatria, 30(Suppl 1), S16–S23. https://doi.org/10.1590/S1516-44462008000500005
11. Verplanken, B., Herabadi, A. G., Perry, J. A., & Silvera, D. H. (2005). Consumer style and health: The role of impulsive buying in unhealthy eating. Psychology & Health, 20(4), 429–441. https://doi.org/10.1080/08870440412331337084
12. Vaidyam, A. N., Torous, J., & Black, D. W. (2024). Experiences with large language model chatbots for mental health: A qualitative study. arXiv preprint arXiv:2401.14362. https://arxiv.org/abs/2401.14362
13. Dartmouth College. (2025, March). First therapy chatbot trial yields mental health benefits. Dartmouth News. https://home.dartmouth.edu/news/2025/03/first-therapy-chatbot-trial-yields-mental-health-benefits
14. OM1. (2023). People are using ChatGPT as a therapist. Mental health experts have some concerns. OM1 Insights. https://www.om1.com/resource/people-are-using-chatgpt-as-a-therapist-mental-health-experts-have-some-concerns


### 6.3. Operational Data (운영 데이터)

* **User History:** 사용자와의 대화 내역은 **Firestore**의 `user/sessions/messages` 컬렉션에 암호화되어 저장됩니다.
* **Session State:** LangGraph의 `checkpointer`를 통해 대화의 문맥(Context)과 상태를 유지합니다.

### 6.2. Open Source

* **Backend**
  * LangChain: <https://www.langchain.com>
  * LangGraph: <https://www.langchain.com/langgraph>
  * FastAPI: <https://fastapi.tiangolo.com>
  * Firebase Admin SDK: <https://firebase.google.com/?hl=ko>
  * RAG
    * Pinecone SDK: <https://www.pinecone.io>
    * Qwen/Qwen3-Embedding-0.6B(RAG Embedding Model): <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>
    * 인덱싱 (본 깃허브 소스코드에는 인덱싱 과정이 포함되어 있지 않으나 아래 패키지를 이용함)
      * LangChain/DocumentLoader/PyMuPDF4LLMLoader: <https://docs.langchain.com/oss/python/integrations/document_loaders/pymupdf4llm>
      * LangChain/DocumentLoader/PyPDF: <https://docs.langchain.com/oss/python/integrations/document_loaders/pypdfloader>
* **Frontend**
  * Jetpack Compose: <https://developer.android.com/compose>
  * Retrofit2: <https://square.github.io/retrofit/>
  * OkHttp: <https://square.github.io/okhttp/>
  * Hilt: <https://dagger.dev/hilt/>, <https://developer.android.com/training/dependency-injection/hilt-android?hl=ko>
  * Coroutines: <https://kotlinlang.org/docs/coroutines-overview.html#coroutine-concepts>
