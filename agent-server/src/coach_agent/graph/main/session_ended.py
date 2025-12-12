# coach_agent/graph/main/session_ended.py

from langchain_core.messages import AIMessage
from coach_agent.graph.state import State

def session_ended(state: State) -> dict:
    """
    state.exit == True인,
    이미 종료된 세션에 사용자가 접근했을 때 실행되는 노드.
    안내 메시지를 보내고 그래프를 즉시 종료한다.
    """
    print("\n=== [DEBUG] SessionEnded Node Triggered ===")
    
    # 프론트엔드에서 모달을 띄우거나 특별한 처리를 할 수 있도록 특정 텍스트나 메타데이터를 포함할 수도 있음
    message_content = "이 상담은 이미 종료되었어요! 🦊\n다른 채팅방을 이용해 주시거나, 다음 주차 상담을 기다려 주세요."
    
    return {
        "messages": [AIMessage(content=message_content)]
    }