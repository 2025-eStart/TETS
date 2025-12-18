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

Lucie/
├─ README.md
├─ README.install.md
├─ GroundRule.md
├─ agent-server/                         # AI 코칭 백엔드
│  ├─ requirements.txt
│  ├─ src/
│  │  ├─ main.py                         # FastAPI 서버 엔트리
│  │  ├─ coach_agent/                    # 코칭 에이전트 핵심
│  │  │  ├─ settings.py
│  │  │  ├─ configuration.py
│  │  │  ├─ graph/                       # LangGraph 상담 플로우
│  │  │  │  ├─ general/
│  │  │  │  │  ├─ builder.py
│  │  │  │  │  └─ nodes.py
│  │  │  │  ├─ main/
│  │  │  │  │  ├─ builder.py
│  │  │  │  │  ├─ edge.py
│  │  │  │  │  ├─ load_protocol.py
│  │  │  │  │  ├─ load_state.py
│  │  │  │  │  ├─ session_ended.py
│  │  │  │  │  └─ update_progress.py
│  │  │  │  ├─ weekly/
│  │  │  │  │  ├─ builder.py
│  │  │  │  │  ├─ counsel_nodes.py
│  │  │  │  │  ├─ edge.py
│  │  │  │  │  ├─ exit_nodes.py
│  │  │  │  │  ├─ extra_nodes.py
│  │  │  │  │  ├─ greeting_nodes.py
│  │  │  │  │  └─ offtopic.py
│  │  │  │  ├─ _init_.py
│  │  │  │  └─ state.py
│  │  │  ├─ prompts/                    
│  │  │  ├─ protocols/                  # CBT 프로토콜
│  │  │  │  ├─ v2/
│  │  │  │  └─ README.md
│  │  │  ├─ rag/                        
│  │  │  ├─ services/                   # Firestore 등 외부 연동
│  │  │  └─ utils/                      # 공용 유틸
│  │  ├─ static/                        # 정적 리소스
│  │  ├─ tests/
│  │  └─ .github/workflows/
│  └─ .gitignore
│
├─ android-app/                          # Android 클라이언트
│  ├─ README.install.md
│  ├─ build.gradle.kts                   
│  ├─ settings.gradle.kts
│  ├─ gradle.properties
│  ├─ gradlew
│  ├─ gradlew.bat
│  ├─ gradle/
│  └─ app/
│     ├─ build.gradle.kts                # Module(app)
│     ├─ proguard-rules.pro
│     ├─ .gitignore
│     └─ src/
│        ├─ main/
│        │  ├─ AndroidManifest.xml
│        │  ├─ java/com/example/impulsecoachapp/
│        │  │   ├─ MainActivity.kt
│        │  │   ├─ MyApplication.kt
│        │  │   ├─ api/
│        │  │   ├─ data/
│        │  │   ├─ di/
│        │  │   ├─ domain/
│        │  │   ├─ ui/
│        │  │   ├─ utils/
│        │  │   ├─ viewmodel/
│        │  │   └─ worker/
│        │  └─ res/
│        ├─ androidTest/
│        └─ test/
└─ .gitignore


## 3. Data & Open Source Info

### 3.1. Knowledge Base (RAG Data)
본 서비스의 코칭 에이전트는 전문적인 심리 상담을 수행하기 위해, 검증된 학술 논문과 상담 프로토콜을 기반으로 지식 베이스(Knowledge Base)를 구축하였습니다.

* **Data Processing:**
  * 참고 문헌의 핵심 상담 기법을 구조화된 **YAML 프로토콜**로 변환 (`src/coach_agent/protocols/`)
  * **Pinecone Vector DB**에 임베딩하여 RAG(Retrieval-Augmented Generation) 시스템에 활용
  * 사용자의 상황에 맞는 논문 기반의 근거 있는 조언(Evidence-based Advice) 제공

### 3.2. Key References (참고 문헌)
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


### 3.3. Operational Data (운영 데이터)

* **User History:** 사용자와의 대화 내역은 **Firestore**의 `user/sessions/messages` 컬렉션에 암호화되어 저장됩니다.
* **Session State:** LangGraph의 `checkpointer`를 통해 대화의 문맥(Context)과 상태를 유지합니다.

### 3.4. Open Source

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
