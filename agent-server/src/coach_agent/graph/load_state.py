# coach_agent/graph/load_state.py
from datetime import datetime, timezone
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from ..state_types import State
from ..services import REPO
from ..configuration import Configuration

# --- 날짜 계산 헬퍼 함수 ---
def _days_since(ts: Optional[datetime], now: datetime) -> int:
    """ 타임스탬프(ts)가 'now'로부터 며칠 전인지 계산합니다. """
    if not isinstance(ts, datetime):
        return 0 # 마지막 접속 기록이 없으면 (신규 유저) 0일로 처리
    
    # Firestore 타임스탬프와 현재 시간의 timezone 통일
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
        
    delta = (now - ts)
    return delta.days if delta.days > 0 else 0  # 0.5일(12시간) 이상 차이나면 1일로 간주


def load_state(state: State, config: RunnableConfig) -> dict:
    
    # 1. Config & Time 설정
    cfg = Configuration.from_runnable_config(config)
    user_id = cfg.user_id
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
    # DB에 있는 닉네임을 우선 가져옵니다.
    current_nickname = user_data.get("nickname")
    final_last_user_message = raw_last_user_message
    
    # 닉네임이 없고(None) + 사용자가 메시지를 보냈다면 -> 닉네임 설정으로 간주
    if current_nickname is None and raw_last_user_message is not None:
        new_nickname = raw_last_user_message.strip()

        # 유효성 검사 및 기본값
        if not new_nickname or len(new_nickname) > 20:
            new_nickname = "여행자"
            
        # DB 업데이트
        REPO.upsert_user(user_id, {"nickname": new_nickname})
        
        # 로컬 변수 업데이트 (반환을 위해)
        current_nickname = new_nickname
        user_data["nickname"] = new_nickname # user 객체도 최신화
        
        # 메시지 소비 처리 (인사말 생성을 위해 None으로 변경)
        final_last_user_message = None
              
    # --- 5. 미접속 기간 계산 (DB 갱신 *전에* 수행) ---
    last_seen_timestamp = user_data.get("last_seen_at")
    days_since_last_seen = _days_since(last_seen_timestamp, now_utc)
    # --- 6. 현재 주차 및 주간 세션 로드 ---
    current_week = user_data.get("current_week", 1)
    weekly_session = REPO.get_active_weekly_session(user_id, current_week)
    
    return {
        "user_id": user_id,
        "now_utc": now_utc,
        "user": user_data,                   # 닉네임 업데이트 반영됨
        "nickname": current_nickname,        # 닉네임 필드 별도 업데이트
        "last_user_message": final_last_user_message, # 소비되었으면 None
        "days_since_last_seen": days_since_last_seen,
        "current_week": current_week,
        "weekly_session": weekly_session
    }
