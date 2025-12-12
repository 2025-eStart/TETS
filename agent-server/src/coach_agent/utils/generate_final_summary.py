from datetime import datetime, timezone
from coach_agent.graph.state import State
from coach_agent.services.llm import CHAT_LLM # 상담 종료 시 요약을 위해 LLM import
from langchain_core.messages import SystemMessage, HumanMessage

# helper: 주간 상담 종료 전, update_progress에서 최종 요약 생성
def _generate_final_summary(state: State) -> str:
    """
    SubGraph에서 미처 요약되지 않고 남은 messages(recent messages)를
    기존 summary에 통합하여 '최종 요약본'을 리턴합니다.
    """
    current_summary = state.summary or "요약 없음"
    remaining_messages = state.messages or []

    # 남은 메시지가 거의 없으면 기존 요약 그대로 사용
    # (시스템 메시지만 있거나 비어있는 경우 등)
    real_msgs = [m for m in remaining_messages if m.type in ["human", "ai"]]
    if not real_msgs:
        print("[update_progress] 추가로 요약할 메시지가 없습니다.")
        return current_summary

    # 대화 텍스트화
    conversation_text = ""
    for msg in real_msgs:
        role = "내담자" if msg.type == "human" else "상담자"
        conversation_text += f"{role}: {msg.content}\n"

    print(f"[update_progress] LLM 호출: 기존 요약 + 남은 대화({len(real_msgs)}건) 통합 중...")

    # 프롬프트 (SubGraph와 유사하지만 '최종 정리' 뉘앙스)
    prompt = (
        f"너는 전문 상담 요약가이다.\n\n"
        f"[기존 상담 요약 노트]\n{current_summary}\n\n"
        f"[추가된 최근 대화]\n{conversation_text}\n\n"
        "위 '추가된 최근 대화' 내용을 반영하여 '기존 상담 요약 노트'를 업데이트해라.\n"
        "이것이 이번 주차 상담의 최종 기록이 되므로, 상담의 전체 흐름과 결론이 잘 드러나도록 요약해라.\n"
        "감정적인 분석보다는 팩트와 주요 개입 내용 위주로 건조하고 명확하게 작성해라."
    )

    try:
        response = CHAT_LLM.invoke([
            SystemMessage(content="상담 기록을 최종 정리하는 전문가입니다."),
            HumanMessage(content=prompt)
        ])
        return response.content
    except Exception as e:
        print(f"[update_progress] 요약 생성 중 LLM 에러: {e}")
        return current_summary
