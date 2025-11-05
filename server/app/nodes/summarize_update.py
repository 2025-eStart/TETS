from app.state_types import State
from app.services import REPO

def summarize_update(state: dict) -> dict:
    s = State(**state)
    REPO.save_message(s.user_id, s.session_type.lower(), s.current_week, "assistant", s.llm_output or "")
    REPO.update_progress(s.user_id, s.current_week, exit_hit=s.exit)
    return s.model_dump()
