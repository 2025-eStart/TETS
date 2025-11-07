# app/graph/summarize_update.py
from app.state_types import State # [수정]
from app.services.summaries import persist_turn

def summarize_update(state: State) -> State:
    persist_turn(
        state.user_id, 
        state.session_type.lower(), 
        state.current_week, 
        state.last_user_message, # [추가] 사용자의 마지막 메시지 전달
        state.llm_output or "", 
        state.exit
    )
    
    return state