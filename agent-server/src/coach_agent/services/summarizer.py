# coach_agent/services/summarizer.py
import yaml
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from services.llm import get_llm 

def create_session_summary(
    messages: list[BaseMessage], 
    current_week: int,
    title: str,             # [추가] 인자로 받음
    exit_criteria: dict     # [추가] 인자로 받음 (dict 그대로 받아서 내부에서 포맷팅)
) -> str:
    
    # 1. 메시지 전처리 (Transcript 생성)
    chat_transcript = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            chat_transcript += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            chat_transcript += f"Counselor: {msg.content}\n"
    
    if not chat_transcript:
        return ""

    # 2. Exit Criteria를 보기 좋은 문자열(YAML)로 변환
    exit_criteria_str = yaml.dump(exit_criteria, allow_unicode=True, default_flow_style=False)

    # 3. PromptTemplate 정의
    summary_prompt = ChatPromptTemplate.from_template("""
    다음은 {current_week}주차 상담 내용입니다.
    오늘 상담 주제가 '{title}'일 때, 아래 세 가지 항목을 이모지를 활용한 개조식 bullet 형태로 명확하게 요약해 주세요.
    문장 수 제한은 없습니다. 단, 각 항목별로 필요한 정보가 빠짐없이 담기도록 해주세요.

    [대화 내용]
    {chat_transcript}

    [요약 지시사항]

    1. 🧩 **핵심 내용 요약**
       - 오늘 상담 주제인 '{title}'과 직접적으로 연결되는 핵심 대화 내용을 정리해 주세요.
       - 사용자 관점에서 무엇을 이야기했고, 어떤 통찰이 나왔는지 명확하게 정리해 주세요.

    2. 🎯 **Exit Criteria 충족 분석**
       - 이번 주차 상담의 종료 기준(exit criteria):
    {exit_criteria_str}
       
       - 사용자가 대화 중 exit criteria의 각 항목을 어떻게 충족했는지, 아래 형식으로 JSON-like bullet로 분석해 주세요.
       - 예시 형식:
         - `{{'자동사고 분석': '할인을 보면 마음이 조급해져 빨리 사야 할 것만 같다.'}}` 
       - 반드시 **각 exit criteria 항목별로 하나씩** 사용자의 실제 발화를 근거로 작성해 주세요.

    3. 📝 **오늘 사용자가 합의한 과제**
       - 사용자가 오늘 세션에서 스스로 지키기로 한 행동, 연습 과제, 체크리스트 등을 정리해 주세요.
       - 실행 단계가 한눈에 보이도록 구체적으로 bullet 형태로 작성해 주세요.

    [요약]
    """)

    # 4. LLM 호출
    llm = get_llm()
    
    # chain = prompt | llm
    chain = summary_prompt | llm
    
    response = chain.invoke({
        "current_week": current_week,
        "title": title,
        "chat_transcript": chat_transcript,
        "exit_criteria_str": exit_criteria_str
    })
    
    return response.content