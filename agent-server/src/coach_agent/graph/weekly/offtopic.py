# coach_agent/graph/weekly/offtopic.py
from __future__ import annotations
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from coach_agent.graph.state import State
from coach_agent.services.llm import CHAT_LLM


def _extract_last_user_text(messages: list[BaseMessage]) -> Optional[str]:
    """
    messages 리스트에서 마지막 Human(사용자) 메시지의 텍스트만 뽑는다.
    - 없으면 None
    """
    if not messages:
        return None

    # 뒤에서부터 훑어서 human 찾기
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", None)
        if msg_type == "human":
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                return content
            # content가 list 구조일 수 있을 때 안전 처리
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                if parts:
                    return "\n".join(parts)
    return None

def _is_offtopic_for_weekly(state: State, user_text: str) -> bool:
    """
    LLM을 이용해 '이번 발화가 대화 흐름(맥락)에서 벗어났는지' 판단.
    """
    
    # 1. 힌트: AI가 직전에 뭐라고 물었는지 가져오기
    last_ai_text = "(없음 - 대화 시작)"
    # 뒤에서부터 찾아서 가장 최근의 AI 메시지 확보
    for msg in reversed(state.messages):
        if msg.type == "ai":
            last_ai_text = msg.content
            break

    # 2. System Prompt: '주제'보다 '맥락'을 우선시하도록 변경
    system_prompt = (
        "너는 상담 챗봇의 **대화 맥락 판별기(Context Validator)**야.\n"
        "사용자의 발화가 **'현재 진행 중인 대화의 흐름'**이나 **'상담 주제(소비 습관)'**와 "
        "관련이 있는지 판단해야 해.\n\n"
        
        "**[판단 기준 - 우선순위 순]**\n"
        "1. **맥락 연결성 (Context Coherence):**\n"
        "   - 상담사(AI)의 직전 질문이나 요청에 대해 **사용자가 대답하고 있는가?**\n"
        "   - (예: AI가 '어떤 음식을 드셨나요?'라고 물었다면, '치킨을 먹었다'는 ON_TOPIC이다. 돈 얘기가 없어도 됨.)\n"
        "   - 단순한 리액션(네, 아니요, 좋아요, 글쎄요)이나 모르겠다는 대답도 흐름상 자연스러우면 ON_TOPIC이다.\n\n"
        
        "2. **주제 적합성 (Domain Relevance):**\n"
        "   - 맥락과 상관없이 새로운 이야기를 꺼냈을 때, 그 내용이 '소비, 지출, 돈, 습관, 감정, 일상 스트레스' 등 상담과 관련된 것이면 ON_TOPIC이다.\n\n"
        
        "3. **이탈 (OFF_TOPIC):**\n"
        "   - 위 1, 2번에 모두 해당하지 않는 경우.\n"
        "   - 뜬금없이 연예인 이야기, 정치, 스포츠, 코딩 질문 등 상담과 전혀 무관한 화제로 넘어가는 경우.\n\n"
        
        "반드시 다음 중 하나만 출력해:\n"
        "- ON_TOPIC\n"
        "- OFF_TOPIC"
    )

    # 3. Human Prompt: 직전 AI 발화를 같이 보여줌
    human_prompt = (
        f"[상황 정보]\n"
        f"- 현재 주차: {state.current_week}주차\n"
        f"- 상담사의 직전 발화: \"{last_ai_text}\"\n\n"
        
        f"[사용자 발화]\n"
        f"```{user_text}```\n\n"
        "위 사용자 발화가 상담사의 질문에 대한 대답이거나, 상담 흐름상 자연스러운가? (ON_TOPIC / OFF_TOPIC)"
    )

    # 4. LLM 호출
    res = CHAT_LLM.invoke(
        [SystemMessage(content=system_prompt),
         HumanMessage(content=human_prompt)]
    )
    
    # 디버깅용 로그 (필요시 주석 해제)
    # print(f"\n[OffTopic Check]\nQ: {last_ai_text[:50]}...\nA: {user_text}\nResult: {res.content}")

    decision = (res.content or "").strip().upper()
    return decision.startswith("OFF")

def handle_offtopic(state: State) -> Dict[str, Any]:
    """
    Main Graph용 HandleOffTopic 노드.

    역할:
      - WEEKLY 세션일 때, 이번 유저 발화가 '소비 CBT 주간 상담' 주제에서 크게 벗어났는지 판별.
      - ON_TOPIC  → {} 리턴 (아무것도 안 함, 다음 라우터로 진행)
      - OFF_TOPIC → 짧은 안내/리다이렉션 메시지를 보내고 이번 턴 종료.
                    (그래프 상에서는 이 노드 뒤에서 __end__ 로 분기시키면 됨)
    """

    # WEEKLY가 아니면 아무 것도 하지 않음
    if state.session_type != "WEEKLY":
        return {}

    last_user_text = _extract_last_user_text(state.messages)
    if not last_user_text:
        # 유저 발화가 없으면 할 수 있는 게 없음 → 그냥 패스
        return {}

    # 3. 예외 처리: 첫 진입, 명령어, 짧은 인사는 무조건 통과
    
    # (A) 메시지 개수로 판단 (HumanMessage가 1개 이하면 이제 막 시작한 것)
    human_msgs = [m for m in state.messages if isinstance(m, HumanMessage)]
    if len(human_msgs) <= 1:
        print("[HandleOffTopic] 첫 번째 메시지(Init)이므로 검사 건너뜀 -> ON_TOPIC 처리")
        return {}

    # (B) 특정 명령어/트리거 단어 리스트 판단 (필요시 추가)
    bypass_keywords = ["/start", "시작", "안녕", "반가워", "__init__"]
    # 텍스트가 짧고(10자 이하) + 키워드가 포함되어 있다면 패스
    if len(last_user_text) < 10 and any(k in last_user_text for k in bypass_keywords):
        print(f"[HandleOffTopic] 단순 인사/명령어('{last_user_text}') 감지 -> ON_TOPIC 처리")
        return {}

    # LLM으로 오프토픽 여부 판별
    is_offtopic = _is_offtopic_for_weekly(state, last_user_text)

    if not is_offtopic:
        # 주제 안에 있으면 아무 것도 하지 않고 다음 노드로 넘김
        print("[HandleOffTopic] ON_TOPIC → route_phase로 진행")
        return {}

    # 여기까지 왔으면 OFF_TOPIC
    print("[HandleOffTopic] OFF_TOPIC 감지 → 안내 메시지 후 턴 종료")

    week = state.current_week
    agenda = state.agenda or f"{week}주차 상담"

    reply = (
        f"이번 대화는 원래 **{week}주차 주간 상담**이고, 주제는 "
        f"'{agenda}' 에요.\n\n"
        "지금 이야기해준 내용도 중요한 고민이지만, 이 세션에서는 "
        "**소비 습관, 돈/지출, 쇼핑, 충동구매**에 대한 이야기를 중심으로 다루고 있어요.\n\n"
        "만약 지금은 소비/지출 이야기를 이어가고 싶지 않다면,\n"
        "• 이 대화는 여기까지만 진행하고,\n"
        "• 잠깐 쉬었다가 마음의 여유가 생겼을 때 다시 루시와 함께 여행자님의 소비 습관을 탐색해봐요!\n\n"
        "주간 상담을 계속하고 싶다면, 이전에 제가 드린 질문에 대해 답해주시거나,\n"
        "뭘 하면 될지 다시 한 번 질문해주세요! 🦊"
    )

    ai_msg = AIMessage(content=reply)

    return {
        "messages": [ai_msg],
    }