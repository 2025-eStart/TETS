# coach_agent/agent.py
from langgraph.checkpoint.memory import MemorySaver
from coach_agent.build_graph import build_graph
from coach_agent.settings import settings

# 설정값 확인
REPO_BACKEND = settings.REPO_BACKEND
print(f"🤖 [Agent] Checkpointer 모드: {REPO_BACKEND}")

if REPO_BACKEND == "firestore":
    # Firestore 모드일 때만 관련 라이브러리 import (에러 방지)
    from coach_agent.services.firebase_admin_client import get_db
    from langchain_google_firestore import FirestoreSaver

    # 1. Firestore Checkpointer 생성
    db_client = get_db()
    checkpointer = FirestoreSaver(
        client=db_client, 
        collection="langgraph_checkpoints"
    )
    print("🔥 Firestore Checkpointer 연결됨")

else:
    # 2. Memory Checkpointer 생성 (로컬 개발용)
    checkpointer = MemorySaver()
    print("🧠 Memory Checkpointer 사용 (서버 재시작 시 대화 기억 휘발됨)")

# 3. 그래프 컴파일 (선택된 checkpointer 주입)
app = build_graph(checkpointer=checkpointer)