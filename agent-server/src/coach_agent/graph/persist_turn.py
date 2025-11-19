# coach_agent/graph/persist_turn.py
# 메시지 DB에 영구 저장 노드

from state_types import State
from services.history import persist_turn 

def persist_turn_node(state: State) -> dict:
    # state.messages를 DB에 영구 저장하는 로직을 수행
    # 보통은 state.messages 전체가 아니라, 마지막 Human/AI 메시지 쌍만 저장합니다.
    persist_turn(state.messages) 
    return {}