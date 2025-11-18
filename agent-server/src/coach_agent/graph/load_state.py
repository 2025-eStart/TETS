# coach_agent/graph/load_state.py
from datetime import datetime, timezone
from typing import Optional
from state_types import State
from services import REPO
from configuration import Configuration
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

# --- 날짜 계산 헬퍼 함수 ---
def _days_since(ts: Optional[datetime], now: datetime) -> int:
    """ 타임스탬프(ts)가 'now'로부터 며칠 전인지 계산합니다. """
    if not isinstance(ts, datetime):
        # 마지막 접속 기록이 없으면 (신규 유저) 0일로 처리
        return 0
    
    # Firestore 타임스탬프와 현재 시간의 timezone 통일
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
        
    delta = (now - ts)
    
    # 0.5일(12시간) 이상 차이나면 1일로 간주 (선택적)
    return delta.days if delta.days > 0 else 0

# 시그니처가 state와 config를 받도록 변경
def load_state(state: State, config: RunnableConfig) -> State:
    s = state
    
    # config에서 user_id 가져오기 (A의 Configuration 클래스 활용)
    cfg = Configuration.from_runnable_config(config)
    s.user_id = cfg.user_id
    s.now_utc = datetime.now(timezone.utc)

    # 1. REPO에서 유저 메타데이터 로드
    user = REPO.get_user(s.user_id)
    s.user = user  # state에 먼저 저장
    
    # --- 2. Checkpointer가 저장한 messages 리스트에서 마지막 사용자 메시지 추출 ---
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

    # --- 3. [핵심] 닉네임 응답 처리 및 저장 로직 ---
    # 만약 DB에 닉네임이 없고(None), 사용자가 메시지를 보냈다면
    if s.nickname is None and s.last_user_message is not None:
        new_nickname = s.last_user_message.strip() # 이 메시지를 닉네임으로 간주.

        # [사용자 요청] 제대로 대답 안 하면 "여행자"로 기본값 설정
        if not new_nickname or len(new_nickname) > 20: # (예: 너무 길거나 빈칸일 때)
            new_nickname = "여행자"
        # [사용자 요청] 닉네임 변수에 저장 (DB 및 State)
        REPO.update_user(s.user_id, {"nickname": new_nickname})
        s.nickname = new_nickname # state의 닉네임도 즉시 갱신
        
        # [중요] 닉네임 메시지는 "소비"되었으므로,
        # build_prompt가 진짜 인사말을 생성하도록 last_user_message를 다시 None으로 설정
        s.last_user_message = None
        s.user["nickname"] = new_nickname # (DB 갱신으로 인해 user 객체가 바뀌었으므로 s.user도 갱신)
        
    # --- 4. 미접속 기간 계산 (DB 갱신 *전에* 수행) ---
    last_seen_timestamp = user.get("last_seen_at") # 'last_seen_at' 필드 (갱신하기 '전'의 옛날 값)
    s.days_since_last_seen = _days_since(last_seen_timestamp, s.now_utc)  # 옛날 값과 현재 값으로 '미접속 기간'을 먼저 계산
    REPO.last_seen_touch(s.user_id) # 마지막 접속 시간 갱신
    
    # --- 6. 현재 주차 및 주간 세션 로드 ---
    s.current_week = user.get("current_week", 1)
    s.weekly_session = REPO.get_active_weekly_session(s.user_id, s.current_week)
    
    return s
