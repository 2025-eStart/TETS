# coach_agent/graph/weekly/exit_nodes.py
from datetime import datetime, timezone
from langchain_core.messages import AIMessage
from coach_agent.graph.state import State
from coach_agent.services.llm import CHAT_LLM # 상담 종료 시 요약을 위해 LLM import
from coach_agent.utils.generate_final_summary import _generate_final_summary

def exit_node(state: State) -> dict:
    """
    WEEKLY 상담 종료 노드.

    역할:
      - 지금까지의 상담을 전부 요약하고,
      - 이번 주차 homework(state.homework)를 정리해서 제시하고,
      - 세션 종료 플래그/타임스탬프를 업데이트한 뒤
      - 다음 주차를 위해 phase를 GREETING으로 돌려놓는다.
    """

    print("\n=== [DEBUG] EXIT Node Started ===")

    # 1) phase 체크: EXIT가 아니면 아무 것도 안 함
    if state.phase != "EXIT":
        print(f"[EXIT] phase != 'EXIT' (현재: {state.phase!r}) → 스킵")
        return {}

    # 1) 최종 요약 생성
    print("[ExitNode] 최종 요약 갱신을 시작합니다...")
    final_summary = _generate_final_summary(state)
    
    # 2) 갱신된 요약으로 메시지 구성
    week = state.current_week
    agenda = state.agenda or f"{week}주차 상담"

    # 2) 상담 요약 섹션 (final_summary 사용)
    if final_summary:
        summary_section = (
            f"오늘은 **{week}주차 - {agenda}** 상담을 여기까지 진행했어요.\n\n"
            "이번 주 상담에서 정리된 내용을 한 번 같이 되짚어볼게요.\n\n"
            f"{final_summary}\n"
        )
    else:
        summary_section = (
            f"오늘은 **{week}주차 - {agenda}** 상담을 여기까지 진행했어요.\n\n"
            "상담 내용을 바탕으로 한 주를 잘 보내시길 바래요.\n\n"
        )

    # 3) Homework 섹션 (state.homework 사용)
    hw_dict = state.homework or {}
    hw_desc = (hw_dict.get("description") or "").strip()
    hw_examples = hw_dict.get("examples") or []

    if hw_desc:
        homework_lines = [
            "📝 **다음 시간까지 해보면 좋은 과제**",
            f"- {hw_desc}",
        ]

        if hw_examples:
            homework_lines.append("\n예시는 이런 것들이 있을 수 있어요:")
            for ex in hw_examples:
                homework_lines.append(f"- {ex}")

        homework_section = "\n".join(homework_lines) + "\n"
    else:
        # 프로토콜이 아직 homework를 안 주는 주차일 경우 fallback
        homework_section = (
            "이번 주에는 오늘 나눈 이야기들을 일상에서 한두 번 떠올려 보면서,\n"
            "비슷한 상황이 생기면 '지금 내 마음과 생각이 어떤지'를 잠깐 적어보는 것만으로도 충분해요.\n"
        )

    # 4) 마무리 인사 섹션
    closing_section = (
        "\n오늘은 여기까지 정리해 볼게요. 😊\n"
        "다음 상담까지 완벽하게 실천하지 못해도 괜찮아요.\n"
        "조금씩이라도 '내 소비를 바라보는 시선'이 달라지는 게 가장 중요한 변화예요.\n"
        "언제든지 다시 이야기하러 와줘요. 🌱"
    )

    final_text = summary_section + "\n" + homework_section + closing_section
    ai_msg = AIMessage(content=final_text)

    now = datetime.now(timezone.utc)

    return {
        "messages": [ai_msg],
        "summary": final_summary, # 갱신된 최종 요약 반영
        "exit": True,  # weekly 세션 종료 플래그
        "phase": "GREETING",
        "counsel_completed_at": now, # COUNSEL phase 완료 시간
    }