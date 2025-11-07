from app.state_types import State
from app.utils.metrics import score_input_quality

def decide_intervention(state: State) -> State:
    s = state
    s.metrics = score_input_quality(s.last_user_message or "")
    m = s.metrics
    if m["risk"]: level = "L5"
    elif m["completeness"] < 0.5: level = "L1"
    elif m["avoidance"] >= 0.6: level = "L2"
    elif m["contradiction"] >= 0.5: level = "L3"
    elif m["affect"]["anxiety"] >= 0.7: level = "L4"
    else: level = "L1"
    
    s.intervention_level = level
    
    return s
