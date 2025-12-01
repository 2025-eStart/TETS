# coach_agent/services/llm.py

from typing import Any, Dict
import os
from langchain_openai import ChatOpenAI
from coach_agent.services.llm_schemas import CounselorTurn, TechniqueSelection


# ---------------------------
# LLM 인스턴스 공통
# ---------------------------

def _build_chat_llm() -> ChatOpenAI:
    """
    상담/기법 선택에 사용할 공통 Chat LLM 인스턴스.
    - 모델명, 온도 등은 환경 변수 또는 고정값으로 설정.
    """
    model_name_env = os.getenv("OPENAI_MODEL_NAME")
    if model_name_env is not None:
        model_name = model_name_env
    else:
        model_name = "gpt-5-mini"

    temperature_env = os.getenv("OPENAI_TEMPERATURE")
    if temperature_env is not None:
        try:
            temperature = float(temperature_env)
        except ValueError:
            temperature = 0.3
    else:
        temperature = 0.3

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
    )


CHAT_LLM = _build_chat_llm()

# 노드에서 messages를 만들고, 여기서는 “모델 + 스키마”만 제공
LLM_CHAIN = CHAT_LLM.with_structured_output(CounselorTurn, method="function_calling")
TECHNIQUE_SELECTOR = CHAT_LLM.with_structured_output(TechniqueSelection, method="function_calling")


'''
# ---------------------------
# 1) 상담 발화용 체인 (techninque_applier에서 사용)
# ---------------------------

COUNSELOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "너는 CBT 기반 충동/습관적 소비 교정을 돕는 전문 상담가다.\n"
                "아래 정보를 참고하여, 이번 턴에서 선택된 CBT 기법을 활용해 "
                "사용자가 세션 목표에 한 걸음 더 다가가도록 돕는 상담 메시지를 작성하라.\n\n"
                "응답은 반드시 CounselorTurn 스키마에 맞는 JSON으로 반환해야 한다."
            ),
        ),
        (
            "system",
            (
                "세션 목표(session_goal): {session_goal}\n"
                "핵심 작업 태그(core_task_tags): {core_task_tags}\n"
                "선택된 기법(selected_technique): {selected_technique}\n"
                "이 기법의 설명(selected_technique_meta): {selected_technique_meta}\n"
                "RAG 이론 스니펫(rag_snippets): {rag_snippets}\n"
                "세션 진행도(session_progress): {session_progress}\n"
                "이번 턴의 micro_goal: {micro_goal}\n"
            ),
        ),
        (
            "system",
            (
                "아래는 최근 대화 히스토리이다. 이를 참고해 이번 상담 발화를 설계하라.\n"
                "{recent_messages}"
            ),
        ),
        ("human", "{user_input}"),
    ]
)


# CounselorTurn 구조화 출력용 체인
LLM_CHAIN: RunnableSerializable[Dict[str, Any], CounselorTurn] = (
    COUNSELOR_PROMPT
    | CHAT_LLM.with_structured_output(CounselorTurn)
)


# ---------------------------
# 2) 기법 선택용 체인 (select_technique_llm에서 사용)
# ---------------------------

TECHNIQUE_SELECTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "너는 CBT 기반 상담 기법을 선택하는 '기법 코디네이터' 역할을 한다.\n"
                "주어진 세션 목표, core task, 후보 기법 목록, 현재까지의 진행 상황, "
                "사용자 발화, RAG 스니펫을 종합해 이번 턴에 사용할 가장 적절한 CBT 기법을 하나 선택하라.\n\n"
                "응답은 반드시 TechniqueSelection 스키마에 맞는 JSON으로 반환해야 한다."
            ),
        ),
        (
            "system",
            (
                "세션 목표(session_goal): {session_goal}\n"
                "핵심 작업 태그(core_task_tags): {core_task_tags}\n"
                "후보 기법(candidate_techniques): {candidate_techniques}\n"
                "세션 진행도(session_progress): {session_progress}\n"
                "기법 사용 히스토리(technique_history): {technique_history}\n"
                "세션 제약(constraints): {constraints}\n"
                "RAG 이론 스니펫(rag_snippets): {rag_snippets}\n"
            ),
        ),
        (
            "system",
            (
                "아래는 최근 대화 히스토리이다.\n"
                "사용자의 현재 상태, 저항/회피, 인사이트 수준 등을 고려하여 "
                "너무 무겁지 않으면서도 의미 있는 한 걸음을 만들 수 있는 기법을 골라라.\n"
                "{recent_messages}"
            ),
        ),
        ("human", "이번 턴에 사용할 CBT 기법과 micro-goal을 결정해줘."),
    ]
)


TECHNIQUE_SELECTOR: RunnableSerializable[Dict[str, Any], TechniqueSelection] = (
    TECHNIQUE_SELECTOR_PROMPT
    | CHAT_LLM.with_structured_output(TechniqueSelection)
)
'''