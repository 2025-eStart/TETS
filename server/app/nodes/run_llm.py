import os
from app.state_types import State
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"), temperature=0.2)

def run_llm(state: dict) -> dict:
    s = State(**state)
    msgs = [SystemMessage(content=s.prompt["system"]),
            HumanMessage(content=s.prompt["user"])]
    out = _llm.invoke(msgs)
    s.llm_output = out.content
    return s.model_dump()
