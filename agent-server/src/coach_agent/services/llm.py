# coach_agent/services/llm.py
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings
from ..state_types import CounselorTurn

def get_llm():
    return ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.2)

def get_llm_chain() -> Runnable:
    """
    구조화된 출력(CounselorTurn)을 반환하는 LCEL 체인을 생성합니다.
    이 체인은 BaseMessage 리스트를 입력받습니다.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(CounselorTurn)
    
    # 이 체인은 [SystemMessage, HumanMessage, ...] 리스트를 입력받아
    # CounselorTurn 객체를 반환합니다.
    return structured_llm

# [추가] 그래프 노드에서 사용할 미리 빌드된 체인
LLM_CHAIN = get_llm_chain()