from datetime import datetime, timezone
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from coach_agent.utils._days_since import _days_since
from coach_agent.state_types import State
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
    current_nickname = user_data.get("nickname")
    final_last_user_message = raw_last_user_message
    
    # 닉네임 등록 로직
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

    # 5. 미접속 기간 계산
    days_since_last_seen = _days_since(user_data.get("last_seen_at"), now_utc)
    
    # 6. 세션 정보 로드
    current_week = user_data.get("current_week", 1)
    weekly_session = REPO.get_active_weekly_session(user_id, current_week)
    
    # 7. 세션 타입 결정
    if cfg.session_type_override:
        final_session_type = cfg.session_type_override
        print(f"👮‍♂️ [LoadState] API Override: {final_session_type}")
    else:
        final_session_type = user_data.get("session_type", "WEEKLY")
    
    # 8. 진행 중인 스텝 인덱스 복구 (State Persistence)
    saved_step_index = 0
    if weekly_session:
        ckpt = weekly_session.get("checkpoint")
        if isinstance(ckpt, dict):
            saved_step_index = ckpt.get("step_index", 0)
         
    # main.py에서 들어온 초기값 (보통 0)
    current_state_step = getattr(state, "current_step_index", 0)
    
    # [결정적 로직] DB에 저장된 진도가 있다면 복구 (덮어쓰기)
    if saved_step_index > current_state_step:
        final_step_index = saved_step_index
        print(f"📂 [LoadState] DB 데이터 복구: Step {current_state_step} -> {saved_step_index}")
    else:
        final_step_index = current_state_step
        print(f"📂 [LoadState] 현재 상태 유지: Step {final_step_index}")

    # 최종 상태 반환
    return {
        "user_id": user_id,
        "now_utc": now_utc,
        "user": user_data,
        "session_type": final_session_type,
        "nickname": current_nickname,
        "last_user_message": final_last_user_message,
        "days_since_last_seen": days_since_last_seen,
        "current_week": current_week,
        "weekly_session": weekly_session,
        "current_step_index": final_step_index
    }