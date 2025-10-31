# services/protocol.py
from __future__ import annotations

# 데모 단계 흐름(필요 시 자유롭게 수정)
STEP_FLOW = ["intro", "psychoeducation", "baseline", "skill_training", "homework", "summary"]

# 1주차는 예시를 풍부하게 채움. 나머지 주차는 기본 템플릿을 자동 생성해 사용.
WEEK_SCRIPT: dict[int, dict[str, dict]] = {
    1: {
        "intro": {
            "goal": "CBT 프로그램 소개와 목표 합의",
            "script": [
                "안녕하세요. 이번 10주 프로그램은 충동 소비의 **패턴**을 이해하고, "
                "**생각-감정-행동**의 연결을 점검해 실습하는 과정이에요. "
                "먼저 최근 1주 동안 기억나는 소비 장면 한 가지를 떠올려 볼까요?"
            ],
            "homework": [
                "일주일 동안 기억나는 충동 소비 순간 2회 메모(상황/생각/감정/행동)"
            ],
        },
        "psychoeducation": {
            "goal": "충동 소비와 자동사고의 개념 이해",
            "script": [
                "충동 소비 순간에는 보통 **자동사고**가 떠올라요. "
                "예: ‘지금 아니면 못 사’, ‘오늘은 보상해도 돼’. 최근 사례에서 떠오른 문장이 있었나요?"
            ],
            "homework": [
                "자동사고 의심 문장 3개 수집(실제 표현 그대로)"
            ],
        },
        "baseline": {
            "goal": "최근 소비 패턴의 기준선 파악",
            "script": [
                "지난 7일을 돌아보면 소비가 늘던 요일/시간대가 있었나요? "
                "‘장소·사람·감정’ 중 무엇이 특히 영향을 줬는지도 떠올려 봅시다."
            ],
            "homework": [
                "이번 주 ‘소비 시간대/감정’ 1줄 기록(하루 1회)"
            ],
        },
        "skill_training": {
            "goal": "쉬운 1단계 기술: 지연·분리",
            "script": [
                "가장 쉬운 기술부터 연습해요. **5분 지연**과 **장소 분리(앱 닫기/자리에서 일어나기)** 입니다. "
                "최근 사례 하나를 골라, 만약 5분 지연을 했다면 어떤 변화가 있었을까요?"
            ],
            "homework": [
                "충동 시 **5분 지연** 2회 실습 + 결과 한 줄 기록"
            ],
        },
        "homework": {
            "goal": "이번 주 과제 정리·일일 체크 연계",
            "script": [
                "좋아요. 이번 주 실습 과제를 정리해드릴게요. 가능하면 **매일 1회** 짧게 체크인도 해요."
            ],
            "homework": [
                "① 자동사고 문장 3개 수집 ② 5분 지연 2회 실습 ③ 소비-감정 1줄 기록(하루1)"
            ],
        },
        "summary": {
            "goal": "핵심 요약 및 다음 주 예고",
            "script": [
                "오늘 핵심은 **자동사고 인식 + 5분 지연**이었어요. "
                "다음 주엔 ‘균형사고’ 연습으로 이어갈게요. 마무리 전에 오늘 느낀 점 한 줄 남겨주실래요?"
            ],
            "homework": []
        },
    },
}

# 나머지 주차는 공통 템플릿으로 자동 생성
DEFAULT_WEEK_KEYWORDS = {
    "psychoeducation": "핵심 개념 설명과 사례 연결",
    "baseline": "최근 패턴 점검과 촉발 요인 파악",
    "skill_training": "실습 기술 훈련과 적용 리허설",
    "homework": "과제 정리 및 일일 체크 연결",
    "summary": "핵심 요약 및 다음 주 예고",
}

def _make_default_week(week: int) -> dict:
    def txt(step: str) -> str:
        if step == "intro":
            return (f"{week}주차를 시작할게요. 이번 주 목표를 짧게 합의하고, "
                    f"최근 소비 장면 한 가지를 떠올려 보겠습니다. 어떤 장면이 떠오르시나요?")
        elif step == "psychoeducation":
            return (f"{week}주차 개념: {DEFAULT_WEEK_KEYWORDS['psychoeducation']}. "
                    f"방금 떠올린 사례와 연결해 보면 어떤 생각-감정-행동 흐름이 보이나요?")
        elif step == "baseline":
            return (f"{week}주차 기준선: {DEFAULT_WEEK_KEYWORDS['baseline']}. "
                    f"요일/시간대/장소/사람/감정 중에 특히 눈에 띄는 게 있을까요?")
        elif step == "skill_training":
            return (f"{week}주차 기술: {DEFAULT_WEEK_KEYWORDS['skill_training']}. "
                    f"가벼운 상황 하나를 골라 지금 바로 적용해 본다면 무엇을 바꿀 수 있을까요?")
        elif step == "homework":
            return (f"{week}주차 과제를 정리할게요. 다음 주까지 가볍게 실습/기록을 이어가요.")
        elif step == "summary":
            return (f"{week}주차 요약입니다. 오늘 느낀 점 한 줄과 함께 마무리할까요?")
        return ""

    def hw(step: str) -> list[str]:
        if step == "homework":
            return [
                f"{week}주차 실습 2회 기록(간단 메모)",
                "하루 1회 ‘소비-감정 1줄’ 체크",
            ]
        elif step == "skill_training":
            return ["이번 주 기술 2회 실습 + 결과 한 줄"]
        elif step == "baseline":
            return ["패턴 관찰: 요일/시간대/감정 1줄 기록(3회)"]
        elif step == "psychoeducation":
            return ["개념과 관련된 본인 문장 2개 수집"]
        return []

    return {
        step: {
            "goal": DEFAULT_WEEK_KEYWORDS.get(step, f"{week}주차 진행"),
            "script": [txt(step)],
            "homework": hw(step),
        }
        for step in STEP_FLOW
    }

# 1주차 외 나머지 2~10주 템플릿 자동 채우기
for w in range(2, 11):
    WEEK_SCRIPT[w] = WEEK_SCRIPT.get(w) or _make_default_week(w)