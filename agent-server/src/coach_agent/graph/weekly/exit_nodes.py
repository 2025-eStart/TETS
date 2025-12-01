from datetime import datetime, timezone
from langchain_core.messages import AIMessage
from coach_agent.graph.state import State


def exit_node(state: State) -> dict:
    """
    WEEKLY 상담 종료 노드.

    역할:
      - 지금까지의 상담 흐름 요약(state.summary)을 다시 들려주고,
      - 이번 주차 homework(state.homework)를 정리해서 제시하고,
      - 세션 종료 플래그/타임스탬프를 업데이트한 뒤
      - 다음 주차를 위해 phase를 GREETING으로 돌려놓는다.
    """

    print("\n=== [DEBUG] EXIT Node Started ===")

    # 1) phase 체크: EXIT가 아니면 아무 것도 안 함
    if state.phase != "EXIT":
        print(f"[EXIT] phase != 'EXIT' (현재: {state.phase!r}) → 스킵")
        return {}

    week = state.current_week
    agenda = state.agenda or f"{week}주차 상담"

    # 2) 상담 요약 섹션 (state.summary 사용)
    summary_text = (state.summary or "").strip()

    if summary_text:
        summary_section = (
            f"오늘은 **{week}주차 - {agenda}** 상담을 여기까지 진행했어요.\n\n"
            "이번 주 상담에서 정리된 내용을 한 번 같이 되짚어볼게요.\n\n"
            f"{summary_text}\n"
        )
    else:
        summary_section = (
            f"오늘은 **{week}주차 - {agenda}** 상담을 여기까지 진행했어요.\n\n"
            "대화를 통해 당신의 소비 패턴과 감정, 자동사고를 함께 살펴보면서\n"
            "어디서부터 바꾸면 좋을지에 대한 실마리를 조금 잡아본 시간이었어요.\n\n"
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

        # weekly 세션 종료 플래그
        "exit": True,
        "phase": "GREETING",
        # COUNSEL phase 완료 시간
        "counsel_completed_at": now,
    }