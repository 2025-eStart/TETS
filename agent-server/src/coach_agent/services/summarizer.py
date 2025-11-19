# coach_agent/services/summarizer.py
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from services.llm import get_llm # LLM 인스턴스 가져오기

def create_session_summary(messages: list[BaseMessage], current_week: int) -> str:
    """
    State의 메시지 리스트를 받아 LLM을 통해 이번 세션 요약본을 생성합니다.
    """
    # 1. 메시지 전처리 (SystemMessage 제외 등)
    chat_transcript = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            chat_transcript += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            chat_transcript += f"Counselor: {msg.content}\n"
    
    if not chat_transcript:
        return ""

    # 2. 프롬프트 구성
    prompt = f"""
    다음은 {current_week}주차 상담 내용입니다.
    핵심 내용, 사용자의 주요 감정, 달성한 성과를 3문장 내외로 요약해 주세요.
    
    [대화 내용]
    {chat_transcript}
    
    [요약]
    """

    # 3. LLM 호출
    llm = get_llm()
    response = llm.invoke(prompt)
    
    return response.content