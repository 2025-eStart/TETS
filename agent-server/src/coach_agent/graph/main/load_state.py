# coach_agent/main/load_state.py
from datetime import datetime, timezone
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from coach_agent.utils._days_since import _days_since
from coach_agent.graph.state import State
from coach_agent.services import REPO
from coach_agent.configuration import Configuration

def _extract_last_user_message(messages: list) -> Optional[str]:
    """메시지 목록에서 마지막 유저 메시지의 텍스트 내용 추출"""
    if not messages or not isinstance(messages[-1], HumanMessage):
        return None
        
    content = messages[-1].content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text", "")
    return None

def load_state(state: State, config: RunnableConfig) -> dict:
    
    # 1. Config & 기본 정보 설정
    cfg = Configuration.from_runnable_config(config)
    user_id = cfg.user_id
    now_utc = datetime.now(timezone.utc)

    # 2. 유저 정보 로드
    user_data = REPO.get_user(user_id)
    
    # 3. 마지막 사용자 메시지 추출
    raw_last_user_message = _extract_last_user_message(state.messages)
    

    # 4. 닉네임 처리
    current_nickname = "여행자"
    # 입력받으려면 아래처럼
    # current_nickname = user_data.get("nickname")
    final_last_user_message = raw_last_user_message
    
    # 닉네임 등록 로직
    ''' 
    if current_nickname is None and raw_last_user_message is not None:
        input_text = raw_last_user_message.strip()
        
        if input_text == "__init__":
            final_last_user_message = None
        else:
            new_nickname = "여행자" if (not input_text or len(input_text) > 20) else input_text
            
            REPO.upsert_user(user_id, {"nickname": new_nickname})
            
            current_nickname = new_nickname
            user_data["nickname"] = new_nickname
            final_last_user_message = None 
    '''
    # 5. 미접속 기간 계산
    days_since_last_seen = _days_since(user_data.get("last_seen_at"), now_utc)
    
    # 6. 세션 정보 로드
    current_week = int(user_data.get("current_week") or 1)
    weekly_session = REPO.get_active_weekly_session(user_id, current_week)
    
    # 7. 세션 타입 결정
    if cfg.session_type_override:
        # /session/init 결정사항을 최우선으로 따른다
        final_session_type = cfg.session_type_override
        print(f"👮‍♂️ [LoadState] API Override: {final_session_type}")
    else:
        # 테스트/백워드 컴패용 fallback
        final_session_type = (
            state.session_type
            or user_data.get("session_type")
            or "GENERAL"   # 기본은 GENERAL로 두는 게 덜 위험함
        )    
    
    # 최종 상태 반환
    return {
        "user_id": user_id,
        "user_nickname": current_nickname,
        "now_utc": now_utc,
        "user": user_data,
        "session_type": final_session_type,
        "last_user_message": final_last_user_message,
        "days_since_last_seen": days_since_last_seen,
        "current_week": current_week,
        "weekly_session": weekly_session,
    }