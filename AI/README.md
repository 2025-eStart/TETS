# 🦊 AI Coach Module

이 폴더는 **“여우” 코칭 AI**의 프롬프트 설계, 점수 계산, 응답 생성, 자동 평가 워크플로우를 담고 있습니다.  
사용자의 일기·알림·점수를 입력으로 받아 **요약 → 대체행동 추천 → 여우 멘트**를 출력하는 파이프라인을 구현합니다.

---

## 📂 디렉토리 구조

```text
AI/
  configs/
    prompts.yaml             # 시스템/유저 프롬프트 버전, 길이·금칙어 규칙
    eval.yaml                # 평가 샘플 수, 컷오프, 자동체점 옵션
  prompts/
    system/coach.md          # “여우” 톤/가드레일/단락 ≤2 등
    user/coach_templates.md  # 사용자 입력 템플릿(일기+알림 합성 등)
    tools/schemas.json       # (선택) 함수호출/툴 스키마
  bas_scoring/
    questionnaire.json       # BAS 문항(10), 가중치/컷오프
    scorer.py                # BAS 점수 산출/정규화/위험 등급 계산
  coach/
    policy/alternatives.json # 도메인별 대체행동 풀(배달/간식/쇼핑/구독…)
    generator.py             # 프롬프트 조합 및 LLM 호출 래퍼
    postprocess.py           # 개수(5~7개), 길이, 중복/금칙어 필터
  data/
    samples/diary.jsonl      # 익명 일기 샘플
    samples/notif.jsonl      # 알림 샘플
  eval/
    scenarios.jsonl          # 평가 시나리오(IMP/보상민감 등 유형별)
    rubric.md                # 평가 기준 (여우 꼬리멘트/공감/대체행동 수)
    evaluator.py             # LLM-judge 기반 자동 채점, 리포트 생성
    reports/.gitkeep
  inference/
    pipeline.py              # 입력 → 출력 파이프라인
    contract.json            # 백엔드 I/O 스키마 (테스트용)
  tests/
    test_scorer.py
    test_generator.py
    test_pipeline.py
