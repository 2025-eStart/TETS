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
             · 해당 주차 세션 요약(agenda, summary, completed_at)을 세션 문서에 저장
             · user.last_weekly_session_completed_at 갱신
             · user.current_week 등도 필요하다면 갱신

    ⚠️ '다음 주차로 진급', '프로그램 전체 완료' 판단은 따로 처리.
       여기서는 "이 주차 세션이 어떻게 진행되고 있는지" + "요약/메타 저장"까지만 담당.
    """

    print("\n=== [DEBUG] update_progress Node Started ===")

    # -------------------------
    # 1. in-graph 진행도 갱신
    # -------------------------

    new_turn_index = (state.turn_index or 0) + 1

    # session_progress는 그냥 그대로 들고 가되,
    # turn_count는 llm_technique_applier에서만 관리하도록 한다.
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
        # REPO에 이런 메서드를 하나 두는 걸 추천:
        #   def update_user_meta(self, user_id: str, **fields): ...
        try:
            REPO.update_user_meta(
                user_id=user_id,
                last_seen_at=now,
            )
        except AttributeError:
            # 기존 REPO에 update_user_meta가 없다면, 기존 update_user를 써도 됨
            # REPO.update_user(user_id, {"last_seen_at": now})
            pass

        # 2-2) WEEKLY 세션 진행도/요약 저장
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

            # 이번 턴에 세션이 종료되었으면, 요약/agenda/완료시간까지 저장
            if state.exit:
                agenda = state.agenda or f"{current_week}주차 상담"
                summary = state.summary or ""

                # 세션 단위 요약 저장용 메서드 예시
                #   def save_weekly_session_summary(
                #       self, user_id, week, agenda, summary, completed_at
                #   ): ...
                try:
                    REPO.save_weekly_session_summary(
                        user_id=user_id,
                        week=current_week,
                        agenda=agenda,
                        summary=summary,
                        completed_at=now,
                    )
                    print(
                        f"[update_progress] [{current_week}주차] "
                        f"요약/agenda 저장 완료 (agenda={agenda!r})"
                    )
                except AttributeError:
                    # 아직 구현 안 되어 있으면, 기존 save_message나 기타 메서드로 대체 가능
                    print(
                        "[update_progress] REPO.save_weekly_session_summary "
                        "가 아직 구현되어 있지 않습니다."
                    )

                # user 문서에 '마지막 weekly 완료 시각' + 현재 주차 저장
                try:
                    REPO.update_user_meta(
                        user_id=user_id,
                        last_weekly_session_completed_at=now,
                        current_week=current_week,
                    )
                except AttributeError:
                    # 마찬가지로 기존 update_user를 사용할 수도 있음
                    # REPO.update_user(user_id, {
                    #     "last_weekly_session_completed_at": now,
                    #     "current_week": current_week,
                    # })
                    pass

    except Exception as e:
        print(f"[update_progress] 진행 상태/메타 업데이트 중 오류 발생: {e}")

    # -------------------------
    # 3. state에 반영할 값 반환
    # -------------------------

    return {
        "turn_index": new_turn_index,
        "session_progress": new_session_progress,
    }

def persist_turn_node(state: State) -> Dict[str, Any]:
    """
    이 턴에서 발생한 User → AI 메시지 한 쌍을 DB에 영구 저장하는 노드.
    - WEEKLY / GENERAL 공통으로 사용.
    - state.messages[-2], state.messages[-1]가 Human/AI일 때만 저장.
    """

    if not state.user_id:
        print("[persist_turn_node] state.user_id가 None이라 저장을 건너뜁니다.")
        return {}

    if not state.session_type:
        print("[persist_turn_node] state.session_type이 None이라 저장을 건너뜁니다.")
        return {}

    try:
        persist_turn(
            user_id=state.user_id,
            week=state.current_week,
            messages=state.messages,
            session_type=state.session_type,
        )
    except Exception as e:
        print(f"[persist_turn_node] persist_turn 호출 중 오류 발생: {e}")

    return {}

