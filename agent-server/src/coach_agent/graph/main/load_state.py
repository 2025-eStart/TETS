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
    print("\n   [Nodes: LoadState] 시작") # [DEBUG]
    
    # 1. Config & 기본 정보 설정
    cfg = Configuration.from_runnable_config(config)
    user_id = cfg.user_id
    now_utc = datetime.now(timezone.utc)

    # 2. 유저 정보 로드
    user_data = REPO.get_user(user_id)
    
    # 3. 마지막 사용자 메시지 추출
    raw_last_user_message = _extract_last_user_message(state.messages)
    print(f"   [Nodes: LoadState] Raw Last Human Message: '{raw_last_user_message}'") # [DEBUG]

    # 4. 닉네임 처리
    current_nickname = "여행자"
    # 입력받으려면 아래처럼
    # current_nickname = user_data.get("nickname")
    final_last_user_message = raw_last_user_message
    if raw_last_user_message == "__init__":
        print("   [Nodes: LoadState] last human message에서 '__init__' 메시지 감지됨. (필터링 로직 확인 필요)")
    
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
    
    # 6. 세션 타입 결정
    if cfg.session_type_override:
        # /session/init 결정사항을 최우선으로 따름
        final_session_type = cfg.session_type_override
        print(f"👮‍♂️ [Nods: LoadState] API Override 적용: {final_session_type}") # [DEBUG]
    else:
        # 테스트/백워드 컴패용 fallback
        final_session_type = (
            state.session_type
            or user_data.get("session_type")
            or "GENERAL"
        )    
        print(f"   [Nodes: LoadState] DB/State 값 사용: {final_session_type}") # [DEBUG]
        
    # 7. 상담 주차 결정: 주간/일반 모드에 따른 주차 차이는 init_session에서 처리됨
    # 메인 그래프의 update_progress 노드에서 REPO.marked_as_completed 호출, 이 함수 내부에서 REPO.nce_to_next_week 호출함으로써 DB의 user.current_week 값이 갱신됨
    # init_session api에서 주간 상담은 user.current_week 값을 기준으로 새 세션을 만듦
    # 일반 상담은 user.current_week -1 값을 기준으로 새 세션을 만듦
    current_week = int(user_data.get("current_week") or 1)  # 주차
    # program_status = user_data.get("program_status", "active") # 10주 상담 프로그램 이수 여부 "active" | "completed"    
    # if program_status == "completed": current_week = 0  # 완료자는 REPO.marked_as_completed에서 주차 0으로 설정되지만 안전장치
    print(f"   [Nodes: LoadState] 최종 세션 타입: {final_session_type}, 현재 주차: {current_week}") # [DEBUG]
        # load_state 노드 어딘가에 추가해서 확인해보세요
    print(f"DEBUG: Loaded history from DB: {state.technique_history}")
    # 최종 상태 반환
    return {
        "user_id": user_id,
        "user_nickname": current_nickname,
        "now_utc": now_utc,
        "session_type": final_session_type,
        "last_user_message": final_last_user_message,
        "days_since_last_seen": days_since_last_seen,
        "current_week": current_week
    }