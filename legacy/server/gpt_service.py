# ================================
# services/gpt_service.py
# ================================

import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# --- 환경 변수 로드 ---
load_dotenv()

# --- 클라이언트 초기화 ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 공용 설정 ---
SYS = "너는 충동소비 교정을 돕는 CBT 코치야. 반드시 JSON 객체만 반환해."
SCHEMA = """{
  "emotion": "<감정 요약(한 단어~짧은 구)>",
  "spending": "<소비 내용 요약 또는 빈 문자열>",
  "action": "<현실적 대체 행동 1~2개, 쉼표로 구분>"
}"""

# =========================================================
# (1) 단순 요약용: 감정·소비·대체행동 도출 (예: /chat)
# =========================================================
def ask_gpt(message: str) -> Dict[str, str]:
    """
    사용자의 문장을 기반으로 감정, 소비내용, 대체행동을 요약.
    """
    prompt = f"""
아래 스키마로만 JSON을 출력해.
스키마:
{SCHEMA}

조건:
- 말투는 따뜻하고 비판적이지 않게
- 'action'은 구체적인 행동 문장 1~2개, 쉼표로 구분
- 불확실하면 빈 문자열로

사용자 입력: "{message}"
JSON만.
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYS},
            {"role": "user", "content": prompt},
        ],
    )

    text = resp.choices[0].message.content.strip()
    try:
        data = json.loads(text)
    except Exception:
        data = {"emotion": "", "spending": "", "action": ""}

    return {
        "emotion": data.get("emotion", ""),
        "spending": data.get("spending", ""),
        "action": data.get("action", "")
    }


# =========================================================
# (2) 프로토콜 주도형 상담: 주차·단계 기반 JSON 생성
# =========================================================
def _call_llm_json(system: str, prompt: str) -> Dict[str, Any]:
    """
    프로토콜 기반 대화용. ask_gpt()를 호출하지 않고
    직접 LLM에 JSON 객체를 요청한다.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.3,
        top_p=0.9,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )

    text = resp.choices[0].message.content.strip()
    try:
        data = json.loads(text)
    except Exception:
        data = {
            "text": "설명을 이해했어요. 방금 상황에서 어떤 감정이 가장 크게 느껴졌나요?",
            "next_step": None,
            "insight": {"emotion": "", "trigger": [], "note": ""}
        }

    return {
        "text": data.get("text", ""),
        "next_step": data.get("next_step"),
        "insight": data.get("insight", {"emotion": "", "trigger": [], "note": ""})
    }


def ask_protocol_driven(
    week: int,
    step: str,
    user_text: Optional[str],
    history: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    프로토콜(주차×단계) 중심으로 LLM이 상담 질문·안내를 생성.
    - services.protocol의 STEP_FLOW / WEEK_SCRIPT를 직접 참조
    - 현재 단계 기준 '허용 가능한 다음 단계(한 단계 전진만)'를 프롬프트에 명시
    - 모델이 homework/summary로 점프하지 않도록 규칙 고지
    """
    from services.protocol import WEEK_SCRIPT, STEP_FLOW  # ← 프로토콜 파일 반영

    cfg = WEEK_SCRIPT.get(week, {}).get(step, {}) or {}
    goal = cfg.get("goal", "")
    script_list = cfg.get("script", []) or []
    homework_list = cfg.get("homework", []) or []

    # 문자열 준비
    script = " ".join(script_list)
    bullet = " • ".join(homework_list)
    hist = "\n".join((history or [])[-6:]) if history else ""
    user = (user_text or "").strip()

    # STEP_FLOW를 기준으로 허용 가능한 '다음 단계' 계산(최대 한 칸 전진)
    try:
        cur_idx = STEP_FLOW.index(step)
    except ValueError:
        # step이 목록에 없으면 intro로 복구
        step = STEP_FLOW[0]
        cur_idx = 0
    allowed_next = STEP_FLOW[min(cur_idx + 1, len(STEP_FLOW) - 1)]

    system = (
        "역할: CBT 상담가(부드럽고 공감적인 톤). "
        "원칙: 1) 질문은 한 번에 1~2개, 2) 비판 없이 공감, "
        "3) 2~3문장 이내로 짧게, 4) 반드시 JSON 객체만 출력, "
        "5) next_step은 현재 단계에서 '최대 한 단계만' 전진하며 건너뛰지 않는다, "
        "6) 'homework'와 'summary'는 서버가 종료 시점에만 사용하므로 임의로 선택하지 않는다."
    )

    prompt = f"""
[프로토콜]
- 주차: {week}
- 현재 단계: {step}
- 목표: {goal}
- 허용 가능한 다음 단계(최대 한 칸 전진): {allowed_next}

[상담가 참고 스크립트]
{script}

[참고 과제]
{bullet if bullet else "과제 없음"}

[이전 대화 요약(선택)]
{hist}

[사용자 최근 응답]
{user}

[출력 형식(JSON)]
{{
  "text": "<사용자에게 보낼 2~3문장 + 마지막에 질문 1개>",
  "next_step": "<intro|psychoeducation|baseline|skill_training|homework|summary 중 택1 또는 null>",
  "insight": {{
    "emotion": "",
    "trigger": [],
    "note": ""
  }}
}}
"""
    return _call_llm_json(system=system, prompt=prompt)