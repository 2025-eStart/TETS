# coach_agent/agent.py
from build_graph import build_graph
from services.firebase_admin_client import get_db
from langchain_google_firestore import FirestoreSaver

# 1. Firestore Checkpointer 인스턴스 생성

# get_db()로 '클라이언트' 객체를 먼저 가져옵니다.
db_client = get_db() 

# FirestoreSaver는 (클라이언트, "컬렉션이름")을 인자로 받습니다.
checkpointer = FirestoreSaver(
    client=db_client, 
    collection="langgraph_checkpoints"
)

# 2. 기존 build_graph 함수를 호출하여 그래프 컴파일
#    Checkpointer를 주입합니다.
app = build_graph(checkpointer=checkpointer)

# 'app' 변수가 langgraph.json에 의해 export 됩니다.