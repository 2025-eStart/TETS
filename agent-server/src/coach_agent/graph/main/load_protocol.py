# coach_agent/graph/weekly/extra_nodes.py

from typing import Dict, Any
from coach_agent.graph.state import State
from coach_agent.utils.protocol_loader import load_protocol_spec  # ✅ 이 로더를 반드시 사용해야 함

def load_protocol(state: State) -> Dict[str, Any]:
    """
    Weekly Subgraph 진입 시 실행되는 초기화 노드.
    여기서 'weekN.yaml' 파일을 읽어와서 State를 세팅해야 합니다.
    """
    print("\n=== [DEBUG] load_protocol Node Started ===")

    # 1. 현재 주차 확인 (없으면 기본 1주차)
    current_week = state.current_week or 1
    session_type = state.session_type or "GENERAL"
    print(f"[load_protocol] 현재 주차: {current_week}, 세션 타입: {session_type}")
    
    # 2. 프로토콜(YAML) 로드
    """
    db에 저장된 program_status:"completed"를 가져오면 좋지만 DB 접근하지 않고
    program_status에 따라 update되는 값 중 state에 로드한 값을 이용해 간단히 처리
    """
    if current_week == 0 and session_type == "GENERAL":
        print("[load_protocol] 상담 프로그램 완료자이므로 프로토콜 로드 생략")
        return {} # 완료자이므로 프로토콜 로드 안 함
    else:
        try:
            protocol = load_protocol_spec(current_week)
        except Exception as e:
            print(f"[init_weekly_state] 프로토콜 로드 실패 (week={current_week}): {e}")
            return {}

        print(f"[load_protocol] {current_week}주차 프로토콜 로드 성공")
        print(f"[load_protocol] allowed_techniques 개수: {len(protocol.get('allowed_techniques', []))}")

        # 3. State 업데이트 (YAML 내용 → State 필드 매핑)
        return {
            "agenda": protocol.get("agenda"),
            "session_goal": protocol.get("session_goal"),
            "core_task_tags": protocol.get("core_task_tags"),
            "allowed_techniques": protocol.get("allowed_techniques"),
            "success_criteria": protocol.get("success_criteria"),
            "constraints": protocol.get("constraints"),
            "homework": protocol.get("homework")
        }