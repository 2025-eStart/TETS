# coach_agent/services/summaries.py
import re
from services import REPO # [수정] __init__에서 REPO 임포트
from typing import Optional


def score_input_quality(user_text: str):
    text = (user_text or "").strip()
    completeness = 1.0 if len(text) >= 10 else 0.3
    avoidance = 0.7 if re.search(r"(몰라|대충|그냥|암튼)", text) else 0.1
    contradiction = 0.0
    risk = bool(re.search(r"(자해|극단|파산)", text))
    affect = {"anxiety": 0.7 if "불안" in text else 0.2, "shame": 0.3}
    return {"completeness": completeness, "avoidance": avoidance,
            "contradiction": contradiction, "risk": risk, "affect": affect}

# [수정] user_text 파라미터 추가
def persist_turn(user_id: str, session_type: str, week: int, user_text: Optional[str], assistant_text: str, exit_hit: bool):
    # [추가] 사용자의 마지막 메시지를 DB에 저장
    if user_text:
        REPO.save_message(user_id, session_type, week, "user", user_text)
        
    # 어시스턴트의 응답을 DB에 저장
    REPO.save_message(user_id, session_type, week, "assistant", assistant_text or "")
    
    # 세션 진행 상태 업데이트
    REPO.update_progress(user_id, week, exit_hit=exit_hit)
    