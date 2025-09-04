import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt(message: str) -> dict:  # <- 여기 타입 힌트도 바꿔줘요
    prompt = f"""
너는 소비 습관 상담 챗봇이야.
내가 한 소비 내역을 알려줄게. 감정과 소비 항목, 그리고 추천할 대체 행동을 아래 JSON 형식으로 정리해줘.

예시:
입력: 오늘 너무 우울해서 충동적으로 옷을 샀어
출력:
{{
  "emotion": "우울함",
  "spending": "의류 구매",
  "action": "산책하기, 감정 일기 쓰기"
}}

사용자 입력: "{message}"
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 충동 소비를 도와주는 챗봇이야."},
            {"role": "user", "content": prompt}
        ]
    )

    return json.loads(response.choices[0].message.content)