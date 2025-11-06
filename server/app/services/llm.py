from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings

_llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.2)

def chat(system_prompt: str, user_prompt: str) -> str:
    msgs = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    out = _llm.invoke(msgs)
    return out.content