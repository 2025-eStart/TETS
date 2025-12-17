# coach_agent/utils/metrics.py
import re

def score_input_quality(user_text: str) -> dict:
    """
    사용자 입력 텍스트를 분석하여 룰베이스 메트릭과 개입 레벨을 반환합니다.
    """
    text = (user_text or "").strip()
    
    # 1. 기초 메트릭 계산
    completeness = 1.0 if len(text) >= 10 else 0.3
    avoidance = 0.7 if re.search(r"(몰라|대충|그냥|암튼|글쎄)", text) else 0.1
    risk = bool(re.search(r"(자해|극단|파산|죽고|살기 싫)", text)) # 키워드 살짝 보강
    affect = {"anxiety": 0.7 if re.search(r"(불안|무섭|겁나|초조)", text) else 0.2}
    
    # 2. 레벨 결정 로직 (decide_intervention 로직 통합)
    if risk:
        level = "L5_CRISIS"       # 위기 관리
    elif affect["anxiety"] >= 0.7:
        level = "L4_EMPATHY"      # 정서적 지지 우선
    elif avoidance >= 0.6:
        level = "L2_CLARIFY"      # 회피 시 명료화 질문
    elif completeness < 0.5:
        level = "L1_ENCOURAGE"    # 단답형 시 구체화 유도
    else:
        level = "L3_NORMAL"       # 일반적인 CBT 진행 (기존 L3/L1 통합)

    # 3. 결과 반환
    return {
        "metrics": {
            "completeness": completeness, 
            "avoidance": avoidance, 
            "risk": risk, 
            "affect": affect
        },
        "level": level
    }