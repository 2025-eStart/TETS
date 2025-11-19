# coach_agent/build_graph.py
from langgraph.graph import StateGraph, END
from state_types import State
from configuration import Configuration
from graph.load_state import load_state
from graph.route_session import route_session, cond_route_session
from graph.pick_week import pick_week
from graph.build_prompt import build_prompt
from graph.decide_intervention import decide_intervention
from graph.run_llm import run_llm
from graph.update_progress import update_progress
from graph.persist_turn import persist_turn_node
from graph.generate_and_save_summary import generate_and_save_summary
from graph.maybe_schedule_nudge import maybe_schedule_nudge

def build_graph(checkpointer=None):
    """
    LangGraph 빌더.
    - 엔트리 포인트: LoadState
    - 세션 라우팅: WEEKLY / GENERAL (기본 __else__는 BuildPrompt)
    - 공통 꼬리: PersistTurn ->  -> MaybeScheduleNudge -> END
    - 체크포인터를 주입받아 상태 복구 가능
    """
    # checkpointer와 config_schema를 StateGraph에 등록
    g = StateGraph(
        State, 
        checkpointer=checkpointer,
        config_schema=Configuration
    )

    # =======================================================
    # 1. ⚙️ 모든 노드 정의 블록 (Add All Nodes First)
    # =======================================================
    
    # [1-A] 공통 노드
    g.add_node("LoadState", load_state) # 세션 상태 로드
    g.add_node("RouteSession", route_session) # 미접속일&주간상담 완료 여부에 따라 주간상담 세션 / 일반 세션 라우팅
    g.add_node("PickWeek", pick_week) # WEEKLY 흐름에서 주차 선택 시 사용
    
    # [1-B] 본문/LLM 호출 흐름 노드
    g.add_node("DecideIntervention", decide_intervention) # 개입 수준 결정
    g.add_node("BuildPrompt", build_prompt) # LLM 프롬프트 빌드
    g.add_node("RunLLM", run_llm) # LLM 호출 및 응답 처리, exit 플래그 설정
    
    # [1-C] 테일/데이터 관리 노드 (Tail)
    g.add_node("PersistTurn", persist_turn_node) # 메시지 영구 저장(db에 저장)
    g.add_node("UpdateProgress", update_progress) # 진행률 업데이트
    g.add_node("GenerateAndSaveSummary", generate_and_save_summary) # 세션 요약 생성 및 저장
    g.add_node("MaybeScheduleNudge", maybe_schedule_nudge) # 세션 종료 후 Nudge(푸시알림) 예약 스케줄링
    
    # =======================================================
    # 2. 🛣️ 모든 엣지/흐름 정의 블록 (Add All Edges)
    # =======================================================

    # [2-A] 엔트리 포인트 설정
    g.set_entry_point("LoadState")

    # [2-B] 초기 흐름 (LoadState -> 라우팅)
    g.add_edge("LoadState", "RouteSession")
    
    # [2-C] 세션 라우팅 (WEEKLY / GENERAL 등 분기)
    # 조건 분기
    g.add_conditional_edges(
        "RouteSession",
        cond_route_session,
        {
            "WEEKLY": "PickWeek",             # 주간 상담이면 주차 선택으로
            "GENERAL": "DecideIntervention",  # 일반 상담(이미 완료)이면 바로 대화 본문으로
            "__else__": "DecideIntervention", # 기타 예외는 DecideIntervention으로
        },
    )

    # [2-D] WEEKLY 흐름
    g.add_edge("PickWeek", "DecideIntervention")

    # [2-E] 본문 공통 흐름 (대화 루프)
    g.add_edge("DecideIntervention", "BuildPrompt")
    g.add_edge("BuildPrompt", "RunLLM")
    
    # [2-F] 후처리 및 종료 흐름 (Tail)
    
    # 1. RunLLM 이후, 메시지 저장 (필수)
    g.add_edge("RunLLM", "PersistTurn")
    
    # 2. 저장 후, 진행률 업데이트
    g.add_edge("PersistTurn", "UpdateProgress")
    
    # 3. 진행률 업데이트 후, 다음 흐름 분기
    # RunLLM에서 넘어온 state.exit 플래그에 따라 요약 생성/종료 여부 결정 로직이 필요함.
    # (현재 코드에는 조건부 엣지가 누락되어 있으므로, 예시 로직을 가정합니다.)
    
    g.add_conditional_edges(
        "UpdateProgress",
        lambda state: "SUMMARY" if state.exit else "NUDGE", # state.exit 기반으로 분기 가정
        {
            "SUMMARY": "GenerateAndSaveSummary",
            "NUDGE": "MaybeScheduleNudge",
        }
    )
    
    # 4. 종료 및 Nudge 스케줄링
    g.add_edge("GenerateAndSaveSummary", "MaybeScheduleNudge")
    g.add_edge("MaybeScheduleNudge", END) # 모든 턴의 최종 목적지

    return g.compile()
