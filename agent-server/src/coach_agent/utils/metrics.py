import re

def score_input_quality(user_text: str):
    text = (user_text or "").strip()
    completeness = 1.0 if len(text) >= 10 else 0.3
    avoidance = 0.7 if re.search(r"(몰라|대충|그냥|암튼)", text) else 0.1
    contradiction = 0.0   # 데모에선 미사용(나중에 요약 비교)
    risk = bool(re.search(r"(자해|극단|파산)", text))
    affect = {"anxiety": 0.7 if "불안" in text else 0.2, "shame": 0.3}
    return {"completeness": completeness, "avoidance": avoidance,
            "contradiction": contradiction, "risk": risk, "affect": affect}
