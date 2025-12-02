# coach_agent/graph/update_progress.py 
from __future__ import annotations
from coach_agent.graph.state import State
from coach_agent.services.history import persist_turn 
from typing import Dict, Any


def persist_turn_node(state: State) -> Dict[str, Any]:
    """
    이 턴에서 발생한 User → AI 메시지 한 쌍을 DB에 영구 저장하는 노드.
    - WEEKLY / GENERAL 공통으로 사용.
    - state.messages[-2], state.messages[-1]가 Human/AI일 때만 저장.
    """

    if not state.user_id:
        print("[persist_turn_node] state.user_id가 None이라 저장을 건너뜁니다.")
        return {}

    if not state.session_type:
        print("[persist_turn_node] state.session_type이 None이라 저장을 건너뜁니다.")
        return {}

    try:
        print(f"[persist_turn_node] 저장 메시지:\n{state.messages}\n")
        persist_turn(
            user_id=state.user_id,
            week=state.current_week,
            messages=state.messages,
            session_type=state.session_type,
        )
    except Exception as e:
        print(f"[persist_turn_node] persist_turn 호출 중 오류 발생: {e}")

    return {}

