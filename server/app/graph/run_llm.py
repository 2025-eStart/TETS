import os
from app.state_types import State
from app.services.llm import chat
from ._helpers import ensure_state
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"), temperature=0.2)

def run_llm(state: dict) -> dict:
    s = ensure_state(state)
    msgs = [SystemMessage(content=s.prompt["system"]),
            HumanMessage(content=s.prompt["user"])]
    out = _llm.invoke(msgs)
    s.llm_output = out.content
    return s
