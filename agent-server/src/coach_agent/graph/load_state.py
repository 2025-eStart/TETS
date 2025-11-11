# coach_agent/graph/load_state.py
from datetime import datetime, timezone
from state_types import State
from services import REPO
from configuration import Configuration
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

# 시그니처가 state와 config를 받도록 변경
def load_state(state: State, config: RunnableConfig) -> State:
    s = state
    
    # config에서 user_id 가져오기 (A의 Configuration 클래스 활용)
    cfg = Configuration.from_runnable_config(config)
    s.user_id = cfg.user_id
    s.now_utc = datetime.now(timezone.utc)

    # Checkpointer가 저장한 messages 리스트에서 마지막 사용자 메시지 추출
    s.last_user_message = None # 기본값
    if s.messages and isinstance(s.messages[-1], HumanMessage):
        msg_content = s.messages[-1].content
        
        # 'content'가 리스트인 경우, 'text' 항목만 추출
        if isinstance(msg_content, list):
            for item in msg_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    s.last_user_message = item.get("text", "")
                    break
        # 'content'가 이미 문자열인 경우
        elif isinstance(msg_content, str):
            s.last_user_message = msg_content
        
    # 3. REPO에서 유저 메타데이터 로드
    user = REPO.get_user(s.user_id)
    REPO.last_seen_touch(s.user_id)
    s.user = user
    s.current_week = user.get("current_week", 1)
    s.weekly_session = REPO.get_active_weekly_session(s.user_id, s.current_week)
    
    return s
