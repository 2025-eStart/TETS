# coach_agent/graph/rewrite_tone.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from state_types import State
from config import settings

# 말투 변환 전용 가벼운 모델 (gpt-4o-mini 추천)
tone_llm = ChatOpenAI(
    model=settings.OPENAI_TONE_MODEL, 
    temperature=0.4,
    api_key=settings.OPENAI_API_KEY
)

# 페르소나 주입 프롬프트
TONE_PROMPT = """
당신은 "전문 교정 에디터"이자 "동화 작가"입니다.
아래 주어진 [원본 메시지]의 **의미와 핵심 내용은 절대 바꾸지 말고**,
말투만 **"어린왕자의 여우" 캐릭터(루시)**에 맞게 다듬어 주세요.

[캐릭터 가이드라인]
1. **말투:** "~ㅂ니다/습니다"는 절대 쓰지 마세요. 부드러운 **"~요"체**와 반존대를 사용하세요.
2. **톤:** 다정하고, 호기심 많고, 따뜻하게 말하세요. 느낌표(!)나 물결(~)을 적절히 사용하여 생동감을 주세요.
3. **호칭:** 사용자를 "여행자님"이라고 생각하고 말하세요. (필요하다면 넣으세요)
4. **길이:** 원본보다 너무 길어지지 않게 간결하게 다듬으세요.

[원본 메시지]
{original_text}

[수정된 메시지]
(오직 수정된 텍스트만 출력하세요)
"""

def rewrite_tone(state: State) -> dict:
    # 1. RunLLM에서 생성된 원본 텍스트 가져오기
    original_text = state.llm_output
    
    # 방어 코드: 텍스트가 없으면 그냥 패스
    if not original_text:
        return {}

    # 2. 말투 변환 실행
    chain = ChatPromptTemplate.from_template(TONE_PROMPT) | tone_llm
    rewritten_text = chain.invoke({"original_text": original_text}).content

    print(f"🔄 [Tone Polish] Before: {original_text[:30]}... -> After: {rewritten_text[:30]}...")

    # 3. State 업데이트 (중요!)
    # 기존 messages의 마지막(RunLLM이 넣은 것)을 덮어쓰거나 교체해야 함.
    # LangGraph의 messages reducer는 'append'가 기본이므로, 
    # 여기서는 state.messages를 직접 수정하기보다,
    # 'messages' 키로 반환하되, 'id'를 이용해 업데이트하거나(고급),
    # 간단하게는 PersistTurn 전에 state.llm_output을 갱신하고,
    # RunLLM이 messages에 바로 append 하지 않도록 흐름을 조정하는 것이 좋음.
    
    # [전략 수정] 
    # RunLLM은 messages에 append 하지 않고 '임시 저장'만 하고,
    # 이 RewriteTone 노드가 최종적으로 messages에 append 하는 방식이 가장 깔끔함.
    
    return {
        "llm_output": rewritten_text,  # 변환된 텍스트로 갱신
        "messages": [AIMessage(content=rewritten_text)] # 최종 메시지 추가
    }