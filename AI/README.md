AI/
  README.md                   # 이 폴더의 목적/워크플로 한 장 요약
  configs/
    prompts.yaml             # 시스템/유저 프롬프트 버전, 길이/금칙어 규칙
    eval.yaml                # 평가 샘플 수, 컷오프, 자동체점 옵션
  prompts/
    system/coach.md          # “여우” 톤/가드레일/단락 ≤2 등
    user/coach_templates.md  # 사용자 입력 템플릿(일기+알림 합성 등)
    tools/schemas.json       # (선택) 함수호출/툴 스키마
  scoring/
    bas/questionnaire.json   # 8~10문항, 가중치/컷오프
    bas/scorer.py            # 점수 산출(정규화, 리스크 등급)
    rst/mapping.json         # 카테고리 매핑
    rst/scorer.py
  coach/
    policy/alternatives.json # 도메인별 대체행동 풀(배달/간식/쇼핑/구독…)
    generator.py             # 프롬프트 조합/LLM 호출 래퍼
    postprocess.py           # 개수(5~7개), 길이, 중복/금칙어 필터
  data/
    samples/diary.jsonl      # (익명) 일기 샘플
    samples/notif.jsonl      # 알림 샘플
  eval/
    scenarios.jsonl          # 평가 시나리오(IMP/보상민감 등 유형별)
    rubric.md                # “여우 꼬리멘트/공감/대체행동 수” 체크 규칙
    evaluator.py             # 규칙/LLM-judge 자동 채점, 리포트 생성
    reports/.gitkeep
  inference/
    pipeline.py              # 입력(일기+알림+점수) → 출력(요약/대체행동/꼬리멘트)
    contract.json            # 백엔드와의 I/O 스키마(스키마 테스트용)
  tests/
    test_scorer.py
    test_generator.py
    test_pipeline.py
