# coach_agent/graph/decide_intervention.py
from ..state_types import State
from ..utils.metrics import score_input_quality

def decide_intervention(state: State) -> dict:
    s = state
    computed_metrics = score_input_quality(s.last_user_message or "")
    m = computed_metrics
    if m["risk"]:
        level = "L5"
    elif m["avoidance"] >= 0.6:
        level = "L2"
    elif m["completeness"] < 0.5:
        level = "L1"
    elif m["contradiction"] >= 0.5:
        level = "L3"
    elif m["affect"]["anxiety"] >= 0.7:
        level = "L4"
    else:
        level = "L1"

    
    s.intervention_level = level
    
    return {
        "metrics": computed_metrics,
        "intervention_level": level
    }
