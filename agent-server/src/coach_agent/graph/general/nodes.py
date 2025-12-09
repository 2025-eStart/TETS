# coach_agent/graph/general/nodes.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from coach_agent.graph.state import State
from coach_agent.services import REPO
from coach_agent.rag.search import search_cbt_corpus
from coach_agent.services.llm import QA_LLM  # 이건 새로 정의한다고 가정
from coach_agent.utils.protocol_loader import load_homework_block_for_week
from coach_agent.prompts.identity import PERSONA
# --- init ----
def init_general_state(state: State) -> Dict[str, Any]:
    """
    General 상담 모드 진입 시 1회 실행되는 초기화 노드.
    - phase를 'GENERAL'로 세팅
    - general_has_greeted, general_turn_count 기본값 설정
    """

    updates: Dict[str, Any] = {}

    # session_type 설정 # 여기가 general 채팅 불러오기 버그 원인
    if getattr(state, "session_type", None) != "GENERAL":
        updates["session_type"] = "GENERAL"

    # 안내 멘트 발송 여부 플래그
    if getattr(state, "general_has_greeted", None) is None:
        updates["general_has_greeted"] = False

    # 턴 카운트
    if getattr(state, "general_turn_count", None) is None:
        updates["general_turn_count"] = 0

    return updates

# --- greeing ----
def general_greeting(state: State) -> Dict[str, Any]:
    """
    General 상담 시작 안내 멘트.
    - 한 번만 실행되도록 route_general에서 제어.
    """
    greeting_text = (
        "과제나 상담에 대해 궁금한 것을 자유롭게 물어보세요!\n\n"
        "예시)\n"
        "• '지난 주 과제에서 자동사고를 어떻게 쓰면 좋을지 잘 모르겠어요'\n"
        "• '제가 쓴 소비 기록을 같이 봐줄 수 있나요?'\n"
        "• 'CBT에서 자동사고랑 핵심신념이 어떻게 다른지 궁금해요'"
    )

    ai_msg = AIMessage(content=greeting_text)

    return {
        # AddMessages aggregator가 messages에 append해줄 것
        "messages": [ai_msg],
        "general_has_greeted": True,
    }

# --- prepare general answer ----
# helpers
def _extract_last_user_text(state: State) -> Optional[str]:
    """messages에서 마지막 HumanMessage의 text를 추출."""
    messages = getattr(state, "messages", []) or []
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # text 타입 찾아서 사용
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")
    return None

def _build_homework_context_from_protocol(state: State) -> str:
    """
    General 상담에서 사용할 '이번 주차 과제 설명'을
    프로토콜 파일에서 직접 읽어온다.

    - 사용자의 current_week은 Firestore user 문서에서 가져옴.
    - 과제 텍스트 자체는 protocol_loader.load_homework_block_for_week 에서 읽음.
    """
    user_id = getattr(state, "user_id", None)
    if not user_id:
        return ""

    # 1) 유저 정보에서 current_week 가져오기
    try:
        user_doc = REPO.get_user(user_id)
    except Exception as e:
        print(f"[General] get_user 실패: {e}")
        return ""

    current_week = int(user_doc.get("current_week", 1))

    # 2) 프로토콜에서 해당 week의 homework 블록 로드
    homework_text = load_homework_block_for_week(current_week)
    if not homework_text:
        return ""

    # 3) 프롬프트용 텍스트로 래핑
    return (
        f"아래는 이 사용자의 현재 주차(Week {current_week}) 과제 설명입니다.\n"
        f"상담 답변 시, 이 과제를 기준으로 설명하고 예시를 들어주세요.\n\n"
        f"{homework_text}"
    )
# node
def prepare_general_answer(state: State) -> Dict[str, Any]:
    """
    General Q&A용 LLM 프롬프트를 준비하는 노드.
    - 마지막 유저 질문 텍스트
    - 저장된 과제/숙제 요약 (REPO)
    - CBT/CBD RAG 검색 결과
    를 합쳐서 llm_prompt_messages를 구성.
    """
    question_text = _extract_last_user_text(state)
    if not question_text:
        # 유저 질문이 없으면 LLM 호출할 필요가 없음
        print("[General] 마지막 유저 질문이 없어 프롬프트 준비를 건너뜁니다.")
        return {"llm_prompt_messages": []}

    # 1) 과제/숙제 컨텍스트
    homework_ctx = _build_homework_context_from_protocol(state)

    # 2) RAG 검색
    rag_docs = search_cbt_corpus(question_text, top_k=4)
    rag_snippets = []
    for i, doc in enumerate(rag_docs):
        meta = doc.metadata or {}
        source = meta.get("source", f"doc_{i}")
        page = meta.get("page", None)
        header = f"[{source}" + (f" p.{page}]" if page is not None else "]")
        rag_snippets.append(f"{header}\n{doc.page_content}")

    rag_text = ""
    if rag_snippets:
        rag_text = "다음은 CBT/CBD 관련 참고 자료 요약입니다:\n\n" + "\n\n".join(rag_snippets)

    # 3) SystemMessage 구성
    system_text =  PERSONA + (
        "당신은 충동소비/과소비 문제를 다루는 CBT 상담가입니다.\n"
        "[역할]\n"
        "1) 사용자의 과제/숙제 내용과 최근 상담 맥락을 참고하여,\n"
        "   사용자가 헷갈리는 부분을 명확하게 설명해줍니다.\n"
        "2) CBT 이론과 RAG에서 제공된 자료를 활용하되,\n"
        "   사용자가 이해하기 쉬운 언어로 풀어서 답변합니다.\n"
        "3) 과제 수행을 도와주는 구체적인 예시와 가이드를 제공합니다.\n\n"
    )
    if homework_ctx:
        system_text += homework_ctx + "\n\n"

    if rag_text:
        system_text += rag_text + "\n\n"

    system_text += (
        "[답변 시 지켜야 할 원칙]\n"
        "- 과제를 대신 작성하지 말고, 사용자가 스스로 쓸 수 있도록 도와줄 것\n"
        "- CBT의 핵심 개념(상황-생각-감정-행동)을 일관되게 사용할 것\n"
        "- 사용자가 불안을 느끼지 않도록, 지지적이고 현실적인 톤으로 말할 것\n"
    )

    system_msg = SystemMessage(content=system_text)
    user_msg = HumanMessage(content=question_text)

    return {
        "llm_prompt_messages": [system_msg, user_msg],
    }

# --- run_general_llm ----
def run_general_llm(state: State) -> Dict[str, Any]:
    """
    General Q&A LLM 호출 노드.
    - prepare_general_answer에서 만든 llm_prompt_messages를 사용
    - 단순 텍스트 응답을 생성해서 messages에 append
    """
    prompt_messages = getattr(state, "llm_prompt_messages", None) or []
    if not prompt_messages:
        print("[General] llm_prompt_messages가 비어 있어 LLM 호출을 스킵합니다.")
        return {}

    ai_msg = QA_LLM.invoke(prompt_messages)

    # GENERAL_QA_CHAIN이 langchain ChatModel이라면 ai_msg는 AIMessage일 것이고,
    # str을 반환한다면 적절히 AIMessage로 감싸주면 됨.
    if isinstance(ai_msg, str):
        ai_msg = AIMessage(content=ai_msg)

    # 턴 카운트 증가
    current_turn = getattr(state, "general_turn_count", 0) or 0
    new_turn = current_turn + 1

    return {
        "messages": [ai_msg],
        "general_turn_count": new_turn,
        # 다음 턴에서는 새 프롬프트를 만들도록 초기화해줘도 됨
        "llm_prompt_messages": [],
    }

# --- general_exit ----
# def general_exit()