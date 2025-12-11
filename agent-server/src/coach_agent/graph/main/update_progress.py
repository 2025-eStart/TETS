# coach_agent/graph/update_progress.py 
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone
from coach_agent.graph.state import State
from coach_agent.services import REPO
from coach_agent.utils.protocol_loader import load_protocol_spec
from coach_agent.services.history import persist_turn 


def apply_weekly_protocol_to_state(state: State, week: int) -> State:
    """
    주어진 week 에 해당하는 프로토콜을 로드해서
    State 에 반영한 새 인스턴스를 반환.

    - current_week, session_goal, core_task_tags, allowed_techniques,
      blocked_techniques, constraints, agenda, homework 를 채움.
    - criteria_status 는 여기서 건드리지 않고, 나중에 다른 노드에서 갱신.
    """
    proto = load_protocol_spec(week)

    return {
            "current_week": proto["week"],
            "session_goal": proto["session_goal"],
            "core_task_tags": proto["core_task_tags"],
            "allowed_techniques": proto["allowed_techniques"],
            "blocked_techniques": proto["blocked_techniques"],
            "constraints": proto["constraints"],
            "agenda": proto["agenda"],
            "homework": proto["homework"],
            "success_criteria": proto["success_criteria"],
        }
    
def update_progress(state: State) -> Dict[str, Any]:
    """
    Dynamic COUNSEL 루프에서 한 턴이 끝난 뒤,
    세션 진행 상태를 갱신하고 DB에 기록하는 노드.

    1) in-graph 진행도:
       - turn_index를 1 증가
       - (⚠️ turn_count는 llm_technique_applier에서만 관리한다)

    2) DB 진행도 / 메타:
       - 항상: user.last_seen_at 업데이트
       - WEEKLY일 때:
         - REPO.update_progress(user_id, week, exit_hit=state.exit) 호출
         - 만약 이번 턴에 exit == True 이면:
             · 요약 텍스트를 세션 도큐먼트에 저장 (save_session_summary)
             · mark_session_as_completed(user_id, week, completed_at)를 호출하여
               - 세션 status=ended
               - completed_at 기록
               - user.last_weekly_session_completed_at 갱신
               - user.current_week 주차 진급(또는 프로그램 완료 처리)
    """

    print("\n=== [DEBUG] update_progress Node Started ===")

    # -------------------------
    # 1. in-graph 진행도 갱신
    # -------------------------
    new_turn_index = (state.turn_index or 0) + 1
    new_session_progress: Dict[str, Any] = dict(state.session_progress or {})

    # -------------------------
    # 2. DB 진행도 / 메타 업데이트
    # -------------------------
    try:
        user_id = state.user_id
        current_week = state.current_week
        session_type = state.session_type

        if user_id is None:
            raise ValueError("[update_progress] state.user_id가 None입니다.")
        if current_week is None:
            raise ValueError("[update_progress] state.current_week가 None입니다.")

        now = datetime.now(timezone.utc)

        # 2-1) 항상: 유저 last_seen_at 업데이트
        try:
            # FirestoreRepo에 정의된 헬퍼 사용
            if hasattr(REPO, "last_seen_touch"):
                REPO.last_seen_touch(user_id)
            else:
                # fallback: upsert_user 직접 호출
                REPO.upsert_user(user_id, {"last_seen_at": now})
        except Exception as e:
            print(f"[update_progress] last_seen_at 업데이트 중 오류: {e}")

        # 2-2) WEEKLY 세션 진행도/요약/완료 처리
        if session_type == "WEEKLY":
            # (기존 로직 유지) 이번 턴에서 종료 조건을 만족했는지 로그로 남김
            try:
                REPO.update_progress(
                    user_id=user_id,
                    week=current_week,
                    exit_hit=state.exit,
                )
                print(
                    f"[update_progress] [{current_week}주차] "
                    f"진행 상태 업데이트 (exit_hit={state.exit})"
                )
            except Exception as e:
                print(f"[update_progress] REPO.update_progress 호출 중 오류: {e}")

            # 이번 턴에 세션이 종료되었으면, 요약 + 완료 처리
            if state.exit:
                # 요약 텍스트 (없으면 빈 문자열)
                summary_text = (state.summary or "").strip()

                # 1) 세션 요약 저장 (summary 필드)
                try:
                    if hasattr(REPO, "save_session_summary"):
                        REPO.save_session_summary(
                            user_id=user_id,
                            week=current_week,
                            summary_text=summary_text,
                        )
                        print(
                            f"[update_progress] [{current_week}주차] "
                            f"세션 요약 저장 완료"
                        )
                except Exception as e:
                    print(
                        f"[update_progress] REPO.save_session_summary 호출 중 오류: {e}"
                    )

                # 2) 세션 완료 + 주차 진급 <- last_weekly_session_completed_at 를 통해 수행
                try:
                    if hasattr(REPO, "mark_session_as_completed"):
                        REPO.mark_session_as_completed(
                            user_id=user_id,
                            week=current_week,
                            completed_at=now,
                        )
                        print(
                            f"[update_progress] [{current_week}주차] "
                            f"mark_session_as_completed 호출 (주차 진급 포함)"
                        )
                except Exception as e:
                    print(
                        f"[update_progress] REPO.mark_session_as_completed 호출 중 오류: {e}"
                    )

    except Exception as e:
        print(f"[update_progress] 진행 상태/메타 업데이트 중 오류 발생: {e}")

    # -------------------------
    # 3. state에 반영할 값 반환
    # -------------------------
    return {
        "turn_index": new_turn_index,
        "session_progress": new_session_progress,
    }


