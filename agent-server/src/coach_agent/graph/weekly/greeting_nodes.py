# coach_agent/graph/weekly/greeting_nodes.py

from typing import Any, Dict
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from coach_agent.graph.state import State

def greeting(state: State) -> dict: # 첫 인사 (첫 턴)
    print("   [WeeklyNode: Greeting] Greeting 노드 실행됨") # [DEBUG]
    
    # 닉네임이 없으면 무조건 "여행자"
    name = state.user_nickname or "여행자"
    week = state.current_week
    agenda = state.agenda or "이번 주 소비 관련 주제"
    goal_text = (
        getattr(state, "goal_text", None)
        or state.session_goal
        or "이번 주차 목표"
    )

    content = (
        f"{name}님, 안녕하세요! {state.current_week}주차 상담을 시작할게요.\n"
        f"오늘은 '{agenda}'를 중심으로, "
        f"'{goal_text}'에 한 걸음 다가가보는 시간을 가져볼게요."
    )

    print(f"   [WeeklyNode: Greeting] 생성된 메시지: {content[:30]}...") # [DEBUG]
    ai_msg = AIMessage(content=content)

    return {
        "messages": [ai_msg],
        "phase": "COUNSEL",
        "weekly_turn_count": state.weekly_turn_count + 1,
    }

''' # 닉네임 입력 로직 삭제
def ask_nickname(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    닉네임이 없는 첫 사용자에게 닉네임을 물어보는 노드.
    - LLM 호출 없이 하드코딩된 멘트만 보냄.
    - 실행 후 세션 종료(exit=True).
    """
    user_id = state.user_id

    # 1) 사용자에게 보낼 메시지 구성
    content = (
        "처음 만나서 반가워요! 😊\n"
        "앞으로 편하게 불러 줄 수 있는 닉네임을 하나 알려줄래요?\n\n"
        "예시: '하늘', '초코', '민지' 처럼 1~2단어로 적어주면 좋아요.\n"
        "'닉네임만' 입력해주세요!\n"
    )

    ai_msg = AIMessage(content=content)

    # 3) state 업데이트: messages에 추가 + exit 플래그
    return {
        "messages": [ai_msg],
        "exit": True,
        "phase": "GREETING",
    }
'''