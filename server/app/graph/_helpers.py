from app.state_types import State
def ensure_state(x) -> State:
    return x if isinstance(x, State) else State(**x)
