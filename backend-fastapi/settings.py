# settings.py
DEMO_MODE = True                 # 데모에서는 RAG/툴 호출 없이 프로토콜 주도형만 사용
LLM_GEN = {"temperature": 0.3, "top_p": 0.9}
SESSION_LIMIT_MIN = 20           # 안내용(로직엔 미사용 가능)
SESSION_MAX_TURNS = 10           # 데모에서는 턴 수로 세션 길이 제한