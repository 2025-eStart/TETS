from app.state_types import State
from ._helpers import ensure_state

SYSTEM = (
"You are a CBT counselor.\n"
"Current phase: Week {week} - {title}\n"
"Goals: {goals}\n"
"Steps allowed: {steps}\n"
"Do not leave the protocol. One or two questions at a time.\n"
"InterventionLevel={level}\n"
)

def build_prompt(state: dict) -> dict:
    s = ensure_state(state)
    spec = s.protocol
    level = s.intervention_level or "L1"
    s.prompt = {
        "system": SYSTEM.format(
            week=spec["week"], title=spec["title"],
            goals="; ".join(spec["goals"]),
            steps=" → ".join(spec["script_steps"]),
            level=level
        ),
        "user": (state.get("last_user_message") or spec["prompt_seed"][0]),
        "history": []
    }
    return s
