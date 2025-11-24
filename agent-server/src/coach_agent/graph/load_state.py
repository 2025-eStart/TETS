# coach_agent/graph/load_state.py
from datetime import datetime, timezone
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from coach_agent.utils._days_since import _days_since
from coach_agent.state_types import State
from coach_agent.services import REPO
from coach_agent.configuration import Configuration

def load_state(state: State, config: RunnableConfig) -> dict:
    
    # --- 1. Config 로드 & Time 설정 ---
    # Config: (main.py -> configuration.py -> 여기서 사용)
    cfg = Configuration.from_runnable_config(config)
    user_id = cfg.user_id # 안드로이드가 보낸 ID가 여기 들어옴
    now_utc = datetime.now(timezone.utc)

    # --- 2. REPO에서 유저 메타데이터 로드 ---
    user_data = REPO.get_user(user_id)
    
    # --- 3. 마지막 사용자 메시지 추출 (계산만 수행) ---
    raw_last_user_message = None
    if state.messages and isinstance(state.messages[-1], HumanMessage):
        msg_content = state.messages[-1].content
        if isinstance(msg_content, list):
            for item in msg_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    raw_last_user_message = item.get("text", "")
                    break
        elif isinstance(msg_content, str):
            raw_last_user_message = msg_content
    
    # --- 4. 닉네임 처리 로직 ---
    # 4-1. DB에 있는 닉네임을 우선 가져옴
    current_nickname = user_data.get("nickname")
    final_last_user_message = raw_last_user_message
    
    # 4-2. 닉네임이 없고(None) + 사용자가 메시지를 보냈다면 -> 닉네임 설정 시도
    if current_nickname is None and raw_last_user_message is not None:
        input_text = raw_last_user_message.strip()
        
        # [Case A] 봇을 깨우는 신호("__init__")인 경우 -> 닉네임 설정 스킵
        if input_text == "__init__":
            # 메시지는 소비된 것으로 처리 (build_prompt로 넘기지 않음)
            final_last_user_message = None
            # 닉네임은 여전히 None -> build_prompt에서 FIXED_NEW_USER_SCRIPT 발동
            
        # [Case B] 사용자가 실제 닉네임(혹은 공백)을 입력한 경우
        else:
            # 빈칸이거나 유효하지 않거나 너무 길면 "여행자"로 설정
            if not input_text or len(input_text) == 0 or len(input_text) > 20: 
                new_nickname = "여행자"
            else:
                new_nickname = input_text

            # DB 업데이트
            REPO.upsert_user(user_id, {"nickname": new_nickname})
            
            # 로컬 변수 업데이트
            current_nickname = new_nickname
            user_data["nickname"] = new_nickname
            
            # 닉네임을 입력한 턴의 메시지는 소비 처리 (인사말 생성을 위해)
            final_last_user_message = None
              
    # --- 5. 미접속 기간 계산 (DB 갱신 *전에* 수행) ---
    last_seen_timestamp = user_data.get("last_seen_at")
    days_since_last_seen = _days_since(last_seen_timestamp, now_utc)
    
    # --- 6. 현재 주차 및 주간 세션 로드 ---
    current_week = user_data.get("current_week", 1)
    weekly_session = REPO.get_active_weekly_session(user_id, current_week)
    
    # --- 7. 세션 타입 결정 로직 ---
    if cfg.session_type_override:
        # API 서버가 시키는 대로 설정 (WEEKLY or GENERAL)
        final_session_type = cfg.session_type_override
        print(f"👮‍♂️ [LoadState] API Override: {final_session_type}") # 디버깅
    else:
        # API 지시가 없으면 DB나 기본값 사용 (기존 로직)
        final_session_type = user_data.get("session_type", "WEEKLY")
    
    
    return {
        "user_id": user_id,
        "now_utc": now_utc,
        "user": user_data,                   # 닉네임 업데이트 반영됨
        "session_type": final_session_type,  # 결정된 세션 타입 저장
        "nickname": current_nickname,        # 닉네임 필드 별도 업데이트
        "last_user_message": final_last_user_message, # 소비되었으면 None
        "days_since_last_seen": days_since_last_seen,
        "current_week": current_week,
        "weekly_session": weekly_session
    }
