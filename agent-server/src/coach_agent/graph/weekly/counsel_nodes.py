# coach_agent/graph/counsel_nodes.py

from __future__ import annotations
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
from coach_agent.graph.state import State
from coach_agent.prompts.identity import COMMON_IDENTITY
from coach_agent.services.llm import TECHNIQUE_SELECTOR, LLM_CHAIN, CHAT_LLM
from coach_agent.utils.protocol_loader import load_techniques_catalog
from coach_agent.rag.search import search_cbt_corpus  # ← 네 RAG 모듈에 맞게 import 수정

# === summarizing helpers ===
def _serialize_recent_messages(
    messages: List[BaseMessage],
    max_turns: int = 6,
) -> str:
    """
    프롬프트에 넣기 위한 '최근 대화 요약 텍스트' 생성.
    - 전체 히스토리를 건드리지 않고, 마지막 max_turns 개만 텍스트로 직렬화
    - Human/AI 중심으로 role 라벨을 붙여준다.
    """
    if not messages:
        return ""

    sub = messages[-max_turns:]
    lines: List[str] = []

    for msg in sub:
        role = getattr(msg, "type", "")  # "human", "ai", "system", ...
        if role == "human":
            r = "사용자"
        elif role == "ai":
            r = "상담가"
        else:
            # system / tool 등은 프롬프트에 굳이 안 넣거나, 짧게만
            r = role or "기타"

        content = msg.content
        # content가 list 구조일 수도 있으므로 처리
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)

        lines.append(f"{r}: {content}")

    return "\n".join(lines)

def _summarize_conversation(state: State, new_ai_message: AIMessage) -> str:
    """
    지금까지의 상담 흐름을 bullet 포인트 요약으로 업데이트한다.

    - 기존 state.summary(있으면)를 기반으로 “업데이트”하는 형태
    - 새로 추가된 최근 대화 + 이번 턴 AI 메시지를 참고해서 3~6개의 bullet로 요약
    - state.messages는 절대 삭제/수정하지 않는다. (trim only in prompt)
    """
    existing_summary = (state.summary or "").strip()

    # 요약에 참고할 최근 히스토리 + 이번 턴 AI 메시지
    history_msgs: List[BaseMessage] = list(state.messages[-6:])
    history_msgs.append(new_ai_message)

    history_lines: List[str] = []
    for msg in history_msgs:
        role = getattr(msg, "type", "")
        if role == "human":
            r = "사용자"
        elif role == "ai":
            r = "상담가"
        else:
            r = role or "기타"

        content = msg.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)

        history_lines.append(f"{r}: {content}")

    history_text = "\n".join(history_lines)

    if existing_summary:
        human_prompt = (
            "다음은 지금까지의 상담 요약이에요:\n"
            f"{existing_summary}\n\n"
            "그리고 아래는 이번 턴 포함 최근 대화 일부예요:\n"
            f"{history_text}\n\n"
            "위 정보를 모두 반영해서, 상담 전체 흐름을 3~6개의 bullet 포인트로 한국어로 업데이트해줘.\n"
            "각 bullet은 '- '로 시작하는 한 줄 문장으로 써줘.\n"
            "- 내담자의 핵심 고민\n"
            "- 이번 주차 목표와 현재까지의 진행 상황\n"
            "- 지금까지 사용한 CBT 기법/전략\n"
            "- 내담자가 얻은 인사이트 또는 행동 계획\n"
            "이 네 가지 축이 드러나도록 요약해줘."
        )
    else:
        human_prompt = (
            "아래 상담 대화를 보고, 상담 흐름의 핵심을 3~6개의 bullet 포인트로 한국어로 요약해줘.\n"
            "각 bullet은 '- '로 시작하는 한 줄 문장으로 써줘.\n"
            "- 내담자의 핵심 고민\n"
            "- 이번 주차에서 다룬 내용\n"
            "- 사용한 CBT 기법/전략\n"
            "- 앞으로의 행동/과제 방향\n"
            "이 네 가지 축이 드러나도록 정리해줘.\n\n"
            f"[대화]\n{history_text}"
        )

    messages_for_llm: List[BaseMessage] = [
        SystemMessage(
            content=(
                "너는 CBT 기반 상담 세션의 내용을 요약하는 어시스턴트다.\n"
                "사용자와 상담가의 대화를 보고, 상담 흐름을 이해하기 쉬운 bullet 포인트로 정리한다."
            )
        ),
        HumanMessage(content=human_prompt),
    ]

    summary_ai = CHAT_LLM.invoke(messages_for_llm)
    # 여기서도 summary_ai.content가 list일 가능성은 거의 없지만, 방어적으로 처리해도 됨
    return summary_ai.content if isinstance(summary_ai.content, str) else str(summary_ai.content)

# === counsel_prepare ===
#helper
def _select_candidate_techniques(state: State) -> List[str]:
    """
    이번 턴에서 LLM이 선택할 수 있는 technique 후보 리스트 생성.

    기본 정책:
      - allowed_techniques 전체를 기본 후보로 사용
      - constraints.blocked_techniques 항목이 있으면 제외
      - technique_history를 참고해 과도하게 반복된 기법은 임시 제외
    """

    candidates = list(state.allowed_techniques or [])

    # 1) constraints 기반 필터링
    constraints = state.constraints or {}
    blocked = constraints.get("blocked_techniques", []) or []
    if blocked:
        candidates = [tid for tid in candidates if tid not in blocked]

    # 2) 같은 기법이 너무 반복된 경우 제외 (예: 3번 연속)
    technique_history = state.technique_history or []
    if len(technique_history) >= 3:
        last_three = [h.get("technique_id") for h in technique_history[-3:]]
        if len(set(last_three)) == 1:  # 마지막 3턴 모두 같은 기법이라면 overuse
            overused = last_three[0]
            candidates = [tid for tid in candidates if tid != overused]

    return candidates

#helper
def _build_rag_queries(state: State) -> List[str]:
    """
    CBT/CBD RAG 검색을 위한 쿼리 문자열을 구성.
    """

    queries: List[str] = []

    # 1) 세션 목표 기반
    if state.session_goal:
        queries.append(f"CBT technique for goal: {state.session_goal}")

    # 2) core_task_tags 기반
    if state.core_task_tags:
        merged_tags = " / ".join(state.core_task_tags)
        queries.append(f"CBT interventions for: {merged_tags}")

    # 3) 최근 사용자 발화 기반
    recent_utts: List[str] = []
    for msg in reversed(state.messages):
        if msg.type == "human":
            recent_utts.append(msg.content)
        if len(recent_utts) >= 3:
            break

    if recent_utts:
        combined = " ".join(recent_utts)
        queries.append(f"User situation: {combined[:300]}")

    return queries

#helper
def _retrieve_rag_snippets(queries: List[str], top_k_per_query: int = 4, max_snippets: int = 12) -> List[str]:
    """
    Pinecone 기반 CBT/CBD RAG를 실제로 호출해서 텍스트 스니펫을 가져온다.

    - search_cbt_corpus(query, top_k)를 호출한다고 가정
        - 반환값: LangChain Document 리스트 또는 유사한 dict 객체 리스트
        - 각 결과에서 content/text 필드를 꺼내서 문자열 리스트로 만든다.
    - 네 프로젝트에서 실제 RAG 함수 이름/반환 타입에 맞게
      search_cbt_corpus 호출 부분과 doc.content 접근 부분만 수정하면 된다.
    """

    snippets: List[str] = []

    for query in queries:
        if not query.strip():
            continue

        try:
            # Pinecone RAG 검색 함수
            docs = search_cbt_corpus(query=query, top_k=top_k_per_query)

            for doc in docs:
                # LangChain Document 타입이라고 가정 (doc.page_content)
                # 만약 dict로 되어 있으면 doc["content"]처럼 바꿔주면 됨.
                text = getattr(doc, "page_content", None)
                if text is None and isinstance(doc, dict):
                    text = doc.get("content") or doc.get("text")

                if text:
                    snippets.append(text)

        except Exception as e:
            # RAG 실패해도 전체 플로우가 터지지 않도록 방어
            print(f"[counsel_prepare] RAG 검색 중 에러 발생 (query={query!r}): {e}")

        # 전체 스니펫 개수가 너무 많아지지 않도록 제한
        if len(snippets) >= max_snippets:
            break

    return snippets[:max_snippets]

#node
def counsel_prepare(state: State) -> Dict[str, Any]:
    """
    Dynamic COUNSEL 루프에서 매 턴 시작 직전에 실행되는 준비 노드.
    
    수행 작업:
      - 이번 턴에서 LLM이 선택할 수 있는 candidate_techniques 계산
      - Pinecone RAG에 쿼리 날려 CBT/CBD 이론 스니펫을 가져온다.
      - 결과를 state.candidate_techniques, state.rag_queries, state.rag_snippets에 반영한다.
    """

    print("\n=== [DEBUG] counsel_prepare Node Started ===")

    if state.phase != "COUNSEL":
        print(f"[counsel_prepare] phase != 'COUNSEL' (현재: {state.phase!r}) → 업데이트 없음")
        return {}

    updates: Dict[str, Any] = {}

    # 1) 후보 기법 리스트
    candidate_techniques = _select_candidate_techniques(state)
    if not candidate_techniques:
        print("[counsel_prepare] 경고: candidate_techniques가 비어 있습니다. "
              "allowed_techniques 전체를 사용합니다.")
        candidate_techniques = list(state.allowed_techniques or [])

    updates["candidate_techniques"] = candidate_techniques

    # 2) RAG 쿼리 생성 + Pinecone 검색
    rag_queries = _build_rag_queries(state)
    rag_snippets = _retrieve_rag_snippets(rag_queries)

    # updates["rag_queries"] = rag_queries
    updates["rag_snippets"] = rag_snippets

    print("[counsel_prepare] candidate_techniques:", candidate_techniques)
    print("[counsel_prepare] rag_queries:", rag_queries)
    print(f"[counsel_prepare] rag_snippets_count={len(rag_snippets)}")

    return updates



# ======= selector ========
#helper
def _serialize_recent_messages(messages: List[BaseMessage], max_turns: int = 6) -> List[Dict[str, Any]]:
    """
    LLM에 넘기기 좋도록 최근 메시지를 단순 dict 형태로 직렬화.
    - 역할: "human"/"ai"
    - 내용: content 텍스트

    LangChain 메시지를 그대로 넘겨도 되지만,
    프롬프트 JSON을 깔끔하게 만들고 싶어서 dict로 변환.
    """
    recent: List[Dict[str, Any]] = []

    for msg in messages[-max_turns:]:
        role = "system"
        if msg.type == "human":
            role = "human"
        elif msg.type == "ai":
            role = "ai"

        recent.append(
            {
                "role": role,
                "content": msg.content,
            }
        )
    return recent

#node
def llm_technique_selector(state: State) -> Dict[str, Any]:
    print("\n=== [DEBUG] select_technique_llm Node Started ===")

    if state.phase != "COUNSEL":
        print(f"[select_technique_llm] phase != 'COUNSEL' (현재: {state.phase!r}) → 업데이트 없음")
        return {}

    updates: Dict[str, Any] = {}

    # 1) candidate_techniques 확보 (없으면 allowed_techniques로 fallback)
    candidate_ids = state.candidate_techniques or state.allowed_techniques or []
    if not candidate_ids:
        print("[select_technique_llm] 경고: candidate_techniques와 allowed_techniques가 모두 비어 있습니다.")
        return {}

    # 2) intervention.yaml 카탈로그 로드
    catalog = load_techniques_catalog()

    candidate_defs: List[Dict[str, Any]] = []
    for tid in candidate_ids:
        meta = catalog.get(tid)
        if meta is None:
            print(f"[select_technique_llm] 경고: intervention catalog에 없는 technique_id: {tid!r}")
            continue
        candidate_defs.append(
            {
                "id": tid,
                **meta,
            }
        )

    if not candidate_defs:
        print("[select_technique_llm] 경고: catalog에서 유효한 candidate_defs를 찾지 못했습니다.")
        return {}

    # 3) 최근 메시지 직렬화
    recent_messages = _serialize_recent_messages(state.messages)
    rag_snippets_preview = (state.rag_snippets or [])[:3]
    
    # 4) 여기서 prompt 메시지 직접 구성
    system_content = (
        COMMON_IDENTITY
        + "\n\n"
        "너는 CBT 기반 충동/습관적 소비 교정을 돕는 전문 상담가다.\n"
        "주어진 세션 목표, core task, 후보 기법 목록, 현재까지의 진행 상황, "
        "사용자 발화, RAG 스니펫을 종합해 이번 턴에 사용할 가장 적절한 CBT 기법을 하나 선택하여\n\n"
        "사용자가 세션 목표에 한 걸음 더 다가가도록 돕는 상담 메시지를 작성하라."
        "응답은 반드시 TechniqueSelection 스키마에 맞는 JSON으로 반환해야 한다.\n"
        "TechniqueSelection 스키마는 다음과 같다.\n"
        "- technique_id: 선택한 CBT 기법의 ID (문자열)\n"
        "- micro_goal: 이번 턴에서 달성할 구체적인 목표 (문자열)\n"
        "- reason: 이 선택이 적절한 이유 (문자열)\n\n"
        f"- 세션 목표(session_goal): {state.session_goal}\n"
        f"- 세션 목표(session_goal): {state.session_goal}\n"
        f"- 핵심 작업 태그(core_task_tags): {state.core_task_tags}\n"
        f"- 세션 진행도(session_progress): {state.session_progress}\n"
        f"- 기법 사용 히스토리(technique_history): {state.technique_history}\n"
        f"- 세션 제약(constraints): {state.constraints}\n"
        f"- RAG 이론 스니펫 일부(rag_snippets): {state.rag_snippets[:3]}\n"
        f"- 후보 기법 목록(candidate_techniques): {candidate_defs}\n"
    )

    human_content = (
        "아래는 최근 대화 히스토리야. 사용자의 상태와 저항/회피, 인사이트 수준을 고려해서 "
        "너무 무겁지 않으면서도 의미 있는 한 걸음을 만들 수 있는 CBT 기법을 하나 골라줘.\n\n"
        f"최근 대화 요약(recent_messages): {recent_messages}\n\n"
        "이번 턴에 사용할 CBT 기법과 micro-goal을 결정해줘."
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=human_content),
    ]

    print("[select_technique_llm] LLM 메시지 준비 완료. candidate 개수:", len(candidate_defs))

    # 5) LLM 호출 (이제 messages를 바로 넣음)
    result = TECHNIQUE_SELECTOR.invoke(messages)

    # 6) 결과 해석 및 방어적 처리 (기존 로직 재사용)
    technique_id = result.technique_id
    micro_goal = result.micro_goal
    reason = result.reason

    if not technique_id:
        print("[select_technique_llm] 경고: LLM이 technique_id를 반환하지 않았습니다.")
        return {}

    if technique_id not in catalog:
        print(f"[select_technique_llm] 경고: LLM이 고른 technique_id={technique_id!r}가 catalog에 없습니다.")
        fallback_id = candidate_ids[0]
        technique_id = fallback_id
        reason = (reason or "") + "\n[FALLBACK] catalog에 없는 기법이라 첫 후보로 대체."

    technique_meta = {
        "id": technique_id,
        **catalog[technique_id],
        "llm_reason": reason,
    }

    updates["selected_technique_id"] = technique_id
    updates["selected_technique_meta"] = technique_meta
    updates["micro_goal"] = micro_goal or ""

    print(f"[select_technique_llm] 선택된 기법: {technique_id}")
    print(f"[select_technique_llm] micro_goal: {updates['micro_goal']!r}")

    return updates


# ===== applier ======
#node
def llm_technique_applier(state: State) -> Dict[str, Any]:
    print("\n=== [DEBUG] llm_technique_applier Node Started ===")

    if state.phase != "COUNSEL":
        print(f"[applier] phase != 'COUNSEL' (현재: {state.phase!r}) → 스킵")
        return {}

    if not state.selected_technique_id:
        print("[applier] selected_technique_id가 없습니다. → 스킵")
        return {}

    # 1) 최근 메시지 직렬화
    recent_messages = _serialize_recent_messages(state.messages)

    # 2) System + Human 메시지 구성
    system_content = (
        COMMON_IDENTITY
        + "\n\n"
        "너는 CBT 기반 충동/습관적 소비 교정을 돕는 전문 상담가다.\n"
        "아래 정보를 참고하여, 이번 턴에서 선택된 CBT 기법을 활용해 "
        "사용자가 세션 목표에 한 걸음 더 다가가도록 돕는 상담 메시지를 작성하라.\n\n"
        "응답은 반드시 CounselorTurn 스키마에 맞는 JSON으로 반환해야 한다.\n\n"
        f"- 세션 목표(session_goal): {state.session_goal}\n"
        f"- 핵심 작업 태그(core_task_tags): {state.core_task_tags}\n"
        f"- 선택된 기법(selected_technique): {state.selected_technique_id}\n"
        f"- 이 기법의 설명(selected_technique_meta): {state.selected_technique_meta}\n"
        f"- RAG 이론 스니펫(rag_snippets): {state.rag_snippets}\n"
        f"- 세션 진행도(session_progress): {state.session_progress}\n"
        f"- 이번 턴의 micro_goal: {state.micro_goal}\n"
        f"- 지금까지의 상담 요약(summary): {state.summary}\n"
        f"- 최근 대화 요약(recent_messages):\n{recent_messages}\n"
    )

    last_user_input = ""
    if state.messages:
        last_msg = state.messages[-1]
        if getattr(last_msg, "type", "") == "human":
            content = last_msg.content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                last_user_input = "\n".join(parts)
            else:
                last_user_input = content

    human_content = (
        "위 정보를 참고해서, 이번 턴에서 사용할 CBT 기법을 실제로 적용하는 상담 메시지를 작성해줘.\n"
        "메시지는 사용자가 바로 읽을 수 있는 한국어 상담 멘트 형태여야 하고, "
        "CounselorTurn 스키마에 맞는 JSON으로 반환해야 해.\n\n"
        f"사용자의 마지막 발화: {last_user_input}"
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=human_content),
    ]

    # 3) LLM 호출 (CounselorTurn 구조)
    structured_output = LLM_CHAIN.invoke(messages)

    response_text = structured_output.response_text
    reasoning = structured_output.reasoning or ""
    progress_delta = structured_output.progress_delta or {}
    criteria_evals = structured_output.criteria_evaluations or []
    llm_suggest = structured_output.suggest_end_session
    llm_session_goals_met = structured_output.session_goals_met

    # 4) technique_history 업데이트
    technique_history = list(state.technique_history or [])
    technique_history.append(
        {
            "technique_id": state.selected_technique_id,
            "micro_goal": state.micro_goal,
            "reasoning": reasoning,
        }
    )

    # 5) session_progress 업데이트
    new_session_progress: Dict[str, Any] = dict(state.session_progress or {})
    # progress_delta 반영
    for key, value in progress_delta.items():
        new_session_progress[key] = value

    # turn_count += 1
    existing_turn_count = new_session_progress.get("turn_count", 0)
    try:
        existing_turn_count = int(existing_turn_count)
    except (TypeError, ValueError):
        existing_turn_count = 0
    new_session_progress["turn_count"] = existing_turn_count + 1

    # 6) criteria_status 업데이트
    criteria_status: Dict[str, bool] = dict(state.criteria_status or {})
    for ev in criteria_evals:
        # CounselorTurn.CriterionEvaluation
        criteria_status[ev.criterion_id] = ev.met
        
    # 7) 이번 턴 AI 메시지 객체 생성
    ai_message = AIMessage(content=response_text)

    # 8) 🔥 요약 갱신 (summary 필드 업데이트)
    new_summary = _summarize_conversation(state, ai_message)

    print("🤖 [applier] LLM Response:")
    print(f"   - Technique: {state.selected_technique_id}")
    print(f"   - Micro goal: {state.micro_goal}")
    print(f"   - Reasoning: {reasoning}")
    print(f"   - Progress delta: {progress_delta}")
    print(f"   - Criteria evals: {[ (e.criterion_id, e.met) for e in criteria_evals ]}")
    print(f"   - turn_count -> {new_session_progress['turn_count']}")
    print(f"   - suggest_end_session: {llm_suggest}, session_goals_met: {llm_session_goals_met}")
    print(f"   - Assistant: {response_text[:120]}...")

    return {
        "messages": [AIMessage(content=response_text)],
        "llm_output": response_text,
        "technique_history": technique_history,
        "session_progress": new_session_progress,
        "criteria_status": criteria_status,
        "llm_suggest_end_session": llm_suggest,
        "summary": new_summary,
    }