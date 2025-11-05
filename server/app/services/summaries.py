import re
from base_repo import REPO

def score_input_quality(user_text: str):
    text = (user_text or "").strip()
    completeness = 1.0 if len(text) >= 10 else 0.3
    avoidance = 0.7 if re.search(r"(몰라|대충|그냥|암튼)", text) else 0.1
    contradiction = 0.0
    risk = bool(re.search(r"(자해|극단|파산)", text))
    affect = {"anxiety": 0.7 if "불안" in text else 0.2, "shame": 0.3}
    return {"completeness": completeness, "avoidance": avoidance,
            "contradiction": contradiction, "risk": risk, "affect": affect}

def persist_turn(user_id: str, session_type: str, week: int, assistant_text: str, exit_hit: bool):
    REPO.save_message(user_id, session_type, week, "assistant", assistant_text or "")
    REPO.update_progress(user_id, week, exit_hit=exit_hit)
