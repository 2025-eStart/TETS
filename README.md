## 이화여자대학교 2025 spring capstone design project – [TETS]

본 레포지토리는  이화여자대학교 컴퓨터공학과 2025년 spring(스타트)-autumn(그로쓰) 캡스톤 디자인 프로젝트로 진행한 **28-e스타트**팀 **[TETS]**의 소스코드와 자료를 정리한 공간입니다.

## 과제명
**ChatGPT API와 RAG, 인지행동치료 기반 상담형 챗봇을 통한, 20대 여성 대상 충동 소비 습관 교정 코칭 서비스**

## 팀명
28-e스타트

## 과제 키워드
챗봇, RAG, ChatGPT API, 충동 소비(Impulse Buying) CBT(Cognitive Behavioral Therapy)

## 📌 프로젝트 개요
본 프로젝트는 20대 여성의 충동 소비 습관을 교정하기 위한 CBT(인지행동치료) 기반 상담형 코칭 앱입니다.
Mitchell et al.(2006)1과 Leite et al.(2014)2의 연구를 참고한 10주차 CBT 프로토콜을 바탕으로, LangGraph를 통해 실제 상담 과정을 대화형 챗봇으로 구현했습니다. 앱은 세 가지 세션으로 구성됩니다.
1. 주간 상담 세션: 각 주차별 CBT 주제(예: Psycho-education, Money Management, Cognitive Restructuring 등)에 따라 사용자의 소비 경험을 탐색하고, 감정·사고·행동 패턴을 재구조화하며 과제를 제시합니다.
2. 일일 체크 세션: 주간 상담에서 제시된 과제의 수행을 돕고, 일상 속 소비 충동과 대처 전략 적용 여부를 짧게 점검합니다.
3. 일반 FAQ 세션: 소비습관 관련 질문에 대해 RAG 기반 근거 응답을 제공합니다.
RAG에는 인지행동치료의 개념, 충동소비와 강박적소비장애의 연관성, 강박적소비장애에 대한 인지행동치료와 그 사례에 대한 논문, 주차별 상담 지침이 포함되어 있습니다.
이 서비스를 통해 사용자는 충동소비의 심리적 원인을 이해하고, 스스로의 소비 패턴을 점진적으로 교정할 수 있습니다.

1. Mitchell, J. E., Burgard, M., Faber, R., Crosby, R. D., & de Zwaan, M. (2006). Cognitive behavioral therapy for compulsive buying disorder. Behaviour Research and Therapy, 44(12), 1859-1865. https://doi.org/10.1016/j.brat.2005.12.009
2. Leite, P. L., Pereira, V. M., Nardi, A. E., & Silva, A. C. (2014). Psychotherapy for compulsive buying disorder: A systematic review. Psychiatry Research, 219(3), 411-419. https://doi.org/10.1016/j.psychres.2014.05.037

## 🗂️ 레포지토리 구성
<pre>
├── server/ # backend, FastAPI 
│   ├── app/
│   │   ├── graph.py            # LangGraph 그래프
│   │   ├── main.py             # FastAPI 서버 진입점
│   │   ├── state_types.py      # LangGraph state
│   │   ├── nodes/              # LangGraph 노드 & 엣지
│   │   ├── rag/                # RAG
│   │   ├── services/           # Firestore, 알림
│   │   └── utils/              
│   │      ├── metrics.py                # 
│   │      └── protocol_loader.py        # 프로토콜 적용
│   ├── protocols/             # protocol_loader.py에서 이용하는 각 주차의 상담 프로토콜 문서
│   │   ├── week01.yaml
│   │   ├── week02.yaml
│   │   ├── week03.yaml
│   │   ├── week04.yaml
│   │   ├── week05.yaml
│   │   ├── week06.yaml
│   │   ├── week07.yaml
│   │   ├── week08.yaml
│   │   ├── week09.yaml
│   │   └── week10.yaml
│   └── settings.py
│   └── requirements.txt
│
├── android-app/ # frontend, Android 모바일 앱
│   ├── app/
│   │   ├── ui/                # 화면 구성
│   │   ├── api/               # 백엔드 연동
│   │   └── utils/             # 알림 수신, 시간대 감지 등
│   └── build.gradle
│
├── legacy/ # 과거 main 브랜치 소스코드 
│   
├── GroundRule.md 
└── README.md 
</pre>
