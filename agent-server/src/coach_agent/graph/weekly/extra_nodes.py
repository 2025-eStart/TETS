from datetime import datetime, timezone
from typing import Dict, Any
from coach_agent.graph.state import State

def init_weekly_state(state: State) -> dict:
    print("\n   [WeeklyNode: Init] Weekly Subgraph 진입 성공") # [DEBUG]
    
    return {
        "phase": "GREETING",
        "weekly_turn_count": 0,
        "turn_index": 0,
        "session_progress": {},
        "technique_history": [],
        "criteria_status": {},
        "candidate_techniques": [],
        "selected_technique_id": None,
        "selected_technique_meta": {},
        "micro_goal": None,
        "rag_queries": [],
        "rag_snippets": [],
        "summary": "",
        "llm_output": None,
        "exit": False,
        # agenda/session_goal/homework 등은 프로토콜 로딩 로직에서 채워줌
    }

def route_phase_node(state: State) -> dict:
    """
    실제로는 아무 것도 안 하고,
    route_phase(라우터 함수)만 쓰기 위한 더미 노드.
    """
    return {}

def should_end_session(state: State) -> Dict[str, Any]:
    """
    COUNSEL path에서 llm_technique_applier 바로 뒤에 호출되는 노드.

    역할:
      - 지금까지의 진행 상황(session_progress, criteria_status, LLM flag)을 바탕으로
        '이번 턴 이후부터 weekly phase를 EXIT로 전환해도 되는지' 판단한다.
      - 종료 조건을 만족하면 phase를 "EXIT"으로 업데이트한다.
      - 아직이면 phase는 건드리지 않는다 (COUNSEL 유지).
    """

    print("\n=== [DEBUG] should_end_session Node Started ===")

    if state.phase != "COUNSEL":
        print(f"[should_end_session] phase={state.phase} → COUNSEL이 아니므로 종료 판단 스킵")
        return {}

    # ---- 1. turn_count 준비 ----
    session_progress = state.session_progress or {}
    existing_turn_count = session_progress.get("turn_count", 0)
    try:
        turn_count = int(existing_turn_count)
    except (TypeError, ValueError):
        turn_count = 0

    constraints: Dict[str, Any] = dict(state.constraints or {})
    # min_turns = constraints.get("min_turns", 3)
    max_turns = constraints.get("max_turns", 12)

    exit_policy_raw = constraints.get("exit_policy")
    exit_policy: Dict[str, Any] = dict(exit_policy_raw or {})

    require_all_criteria = exit_policy.get("require_all_criteria", True)
    # require_min_turns = exit_policy.get("require_min_turns", True)
    require_llm_confirmation = exit_policy.get("require_llm_confirmation", False)

    print(f"[should_end_session] turn_count={turn_count}, "
          # f"min_turns={min_turns}, max_turns={max_turns}"
          )
    print(f"[should_end_session] exit_policy="
          f"(require_all_criteria={require_all_criteria}, "
          # f"require_min_turns={require_min_turns}, "
          f"require_llm_confirmation={require_llm_confirmation})")

    # ---- 2. Max 턴 초과 시: 강제 종료 ----
    if turn_count >= max_turns:
        print("[should_end_session] max_turns 이상 → 강제 종료, phase=EXIT로 전환")
        return {
            "phase": "EXIT",
            "counsel_completed_at": datetime.now(timezone.utc),
        }

    # ---- 3. success_criteria 평가 ----
    success_criteria = state.success_criteria or []
    criteria_status = state.criteria_status or {}

    required_ids = [
        item.get("id")
        for item in success_criteria
        if isinstance(item, dict)
        and item.get("required", False) is True
        and item.get("id") is not None
    ]

    all_required_met = True
    for crit_id in required_ids:
        if criteria_status.get(crit_id) is not True:
            all_required_met = False
            break

    any_required_met = any(criteria_status.get(crit_id) is True for crit_id in required_ids)

    if require_all_criteria:
        criteria_ok = all_required_met
    else:
        criteria_ok = any_required_met if required_ids else True

    print(f"[should_end_session] criteria_ok={criteria_ok}, "
          f"all_required_met={all_required_met}, any_required_met={any_required_met}")

    '''
    # ---- 4. min_turns 조건 ----
    if require_min_turns and turn_count < min_turns:
        print("[should_end_session] min_turns 미달 → 종료 보류, phase 그대로(COUNSEL)")
        return {}
    '''
    # ---- 5. (옵션) LLM 확인 조건 ----
    if require_llm_confirmation:
        llm_suggest = getattr(state, "llm_suggest_end_session", False)
        print(f"[should_end_session] require_llm_confirmation=True, "
              f"llm_suggest_end_session={llm_suggest}")
        if not llm_suggest:
            return {}

    # ---- 6. 최종 결정 ----
    if criteria_ok:
        print("[should_end_session] criteria_ok=True → EXIT phase로 전환")
        return {
            "phase": "EXIT",
            "counsel_completed_at": datetime.now(timezone.utc),
        }

    print("[should_end_session] criteria_ok=False → COUNSEL 유지")
    return {}