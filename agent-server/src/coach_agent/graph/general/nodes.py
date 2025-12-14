# coach_agent/graph/general/nodes.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from coach_agent.graph.state import State
from coach_agent.services import REPO
from coach_agent.rag.search import search_cbt_corpus
from coach_agent.services.llm import CHAT_LLM
from coach_agent.utils.protocol_loader import load_homework_block_for_week
from coach_agent.prompts.identity import PERSONA

# --- init ----
def init_general_state(state: State) -> Dict[str, Any]:
    """
    General 상담 모드 진입 시 1회 실행되는 초기화 노드.
    Dict/Object 호환성 확보
    """
    print("\n🔍 [General] init_general_state 노드 시작")
    
    updates: Dict[str, Any] = {}

    # State 값 가져오기 (Hybrid)
    if isinstance(state, dict):
        current_type = state.get("session_type")
        current_turn = state.get("general_turn_count")
    else:
        current_type = getattr(state, "session_type", None)
        current_turn = getattr(state, "general_turn_count", None)

    # session_type 설정
    if current_type != "GENERAL":
        updates["session_type"] = "GENERAL"
        print(f"🔍 [General] session_type 변경: {current_type} -> GENERAL")

    # 턴 카운트
    if current_turn is None:
        updates["general_turn_count"] = 0
        print("🔍 [General] general_turn_count 0으로 초기화")

    return updates


# --- generate general answer ---
# helpers
# 입력 타입을 State가 아닌 List[Any]로 변경하여 재사용성 및 버그 수정
def _extract_last_user_text(messages: List[Any]) -> Optional[str]:
    """
    메시지 리스트에서 마지막 HumanMessage의 text를 추출.
    """
    if not messages:
        return None
    
    print(f"   [Debug Extractor] 메시지 {len(messages)}개 중 탐색 시작...")

    for i, msg in enumerate(reversed(messages)):
        msg_type = ""
        content = ""

        # 1. Dict 처리
        if isinstance(msg, dict):
            msg_type = msg.get("type", "")
            content = msg.get("content", "")
        # 2. Object 처리
        elif hasattr(msg, "type") and hasattr(msg, "content"):
            msg_type = getattr(msg, "type", "")
            content = getattr(msg, "content", "")
            
        # 디버깅용: 탐색중인 메시지 타입 확인
        # print(f"     Msg[-{i+1}]: type={msg_type}, content_sample={str(content)[:10]}")

        if msg_type == "human":
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                return "\n".join(parts).strip()
            
    return None

def _build_homework_context_from_protocol(state: State) -> str:

    user_id = state.user_id
    if not user_id: return ""

    if state.current_week is None:
        print("[General] _build_homework_context_from_protocol: current_week is None")
        return ""
    else: current_week = state.current_week
    
    homework_text = load_homework_block_for_week(current_week)
    if not homework_text: return ""

    return (
        f"아래는 이 사용자의 현재 주차(Week {current_week}) 과제 설명입니다.\n"
        f"사용자가 과제에 대해 질문을 하거나 혼란스러워할 시, 이 과제를 기준으로 설명하고 예시를 들어주세요.\n\n"
        f"{homework_text}"
    )

# node
def generate_general_answer(state: State) -> Dict[str, Any]:
    """
    General 상담의 답변을 생성
    """
    print("\n🔍 [General] generate_general_answer 노드 시작")
    current_turn = state.general_turn_count or 0
    messages = state.messages
    
    program_status = REPO.get_user(state.user_id).get("program_status", "active")
    print(f"🔍 [General] User Status Directly Fetched: {program_status}") # 값이 없으면 기본값 "active"
    # ---------------------------------------------------------
    # 1. 마지막 메시지 가져오기
    # ---------------------------------------------------------
    last_message = messages[-1]
    print(f"🔍 [General] 마지막 메시지 타입: {type(last_message)}"
          f", 내용 샘플: '{str(last_message.content)[:30]}'" )
    
    # __init__ 메시지 감지 시 고정된 인사말 반환 (LLM 호출 X)
    if last_message.content.strip() == "__init__":
        greeting_text = (
            "과제나 상담에 대해 궁금한 것을 자유롭게 물어보세요!\n\n"
            "예시)\n"
            "• '지난 주 과제에서 자동사고를 어떻게 쓰면 좋을지 잘 모르겠어요'\n"
            "• '제가 쓴 소비 기록을 같이 봐줄 수 있나요?'\n"
            "• 'CBT에서 자동사고랑 핵심신념이 어떻게 다른지 궁금해요'"
        )
        
        # LLM을 거치지 않고 바로 AI 메시지를 반환
        return {
            "messages": [AIMessage(content=greeting_text)]
        }

    # ---------------------------------------------------------
    # 2. 일반적인 경우 (LLM 호출)
    # ---------------------------------------------------------

    # 2-1. 사용자 질문 추출 (수정된 함수 호출)
    # messages 리스트를 넘김
    question_text = _extract_last_user_text(messages)
    
    print(f"🔍 [General] 최종 추출된 질문: '{question_text}'")

    # [예외 처리] 질문을 못 찾은 경우
    if not question_text:
        print("🔍 [General] ❌ 질문 없음 -> Fallback 반환")
        return {
            "messages": [AIMessage(content="죄송해요, 말씀하신 내용을 잘 이해하지 못했어요. 다시 한 번 말씀해 주시겠어요?")],
            "general_turn_count": (current_turn or 0) + 1
        }

    # 2-2. 컨텍스트 준비 (과거 세션 요약 + 숙제 + RAG)
    # 과거 세션 요약 불러오기
    summaries = REPO.get_past_summaries(user_id=state.user_id, current_week=state.current_week or 1)
    past_summary_text = ""
    if summaries:
        # 요약 텍스트 포맷팅
        summary_lines = [f"- Week {s['week']}: {s['summary']}" for s in summaries]
        past_summary_text = "이 사용자의 현재 진행 중인 상담 요약들:\n" + "\n".join(summary_lines)
        print(f"🔍 [General] 과거 세션 요약 불러옴: {len(summaries)}개"
              f", 내용 샘플: '{summary_lines[0][:50]}...'")
        
    # 숙제 불러오기 (상담 프로그램 진행 중인 사용자에 한함)
    if program_status == "active": # 상담 프로그램 진행 중인 사용자에 한함, 프로그램 종료 시 불러오지 않음.
        homework_ctx = _build_homework_context_from_protocol(state)
    
    # RAG 자료 검색
    rag_snippets = []
    try:
        rag_docs = search_cbt_corpus(question_text, top_k=3)
        for doc in rag_docs:
            content = getattr(doc, "page_content", None)
            if content is None and isinstance(doc, dict):
                content = doc.get("content") or doc.get("text")
            if content:
                rag_snippets.append(content)
    except Exception as e:
        print(f"[General] RAG 검색 실패: {e}")

    rag_text = ""
    if rag_snippets:
        rag_text = "참고 자료(CBT 이론):\n" + "\n\n".join(rag_snippets)

    # 2-3. 프롬프트 구성 (System + Human)
    system_text = PERSONA + (
        "당신은 충동소비/과소비 문제를 다루는 CBT 상담가입니다.\n"
        "[역할]\n"
        "1) 사용자의 과제/숙제 내용과 최근 상담 맥락을 참고하여, 사용자가 헷갈리는 부분을 명확하게 설명해줍니다.\n"
        "2) CBT 이론과 RAG 자료를 활용하되, 쉬운 언어로 풀어서 답변합니다.\n"
        "3) 지지적이고 현실적인 톤으로 말하세요.\n\n"
    )
    if past_summary_text:
        system_text += past_summary_text + "\n\n"
    if homework_ctx:
        system_text += homework_ctx + "\n\n"
    if rag_text:
        system_text += rag_text + "\n\n"
        
    system_text += (
        "[답변 원칙]\n"
        "- 과제를 대신 해주지 말고 가이드를 줄 것\n"
        "- 핵심 개념(상황-생각-감정-행동)을 일관되게 사용할 것"
    )

    prompt_messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=question_text)
    ]

    # 2-4. LLM 실행
    print("🔍 [General] LLM 호출 시작...")
    try:
        ai_msg = CHAT_LLM.invoke(prompt_messages)
    except Exception as e:
        print(f"🔍 [General] ❌ LLM 에러: {e}")
        return {
            "messages": [AIMessage(content="죄송합니다. 일시적인 오류로 답변을 생성하지 못했습니다.")]
        }

    if isinstance(ai_msg, str):
        ai_msg = AIMessage(content=ai_msg)

    new_turn = (current_turn or 0) + 1

    print("🔍 [General] ✅ 답변 생성 완료")
    return {
        "messages": [ai_msg],
        "general_turn_count": new_turn
    }