from fastapi import FastAPI, Header, HTTPException
from datetime import datetime, timezone
from dotenv import load_dotenv; load_dotenv()
from app.state_types import State
from app.graph import build_graph

app = FastAPI(title="ImpulseCoach-Server")
GRAPH = build_graph()

@app.get("/health")
def health(): return {"ok": True}

@app.post("/chat/start")
def chat_start(user_id: str):
    s = State(user_id=user_id, now_utc=datetime.now(timezone.utc))
    out = GRAPH.invoke(s)
    return out.model_dump()

@app.post("/chat/send")
def chat_send(user_id: str, user_message: str):
    s = State(user_id=user_id, now_utc=datetime.now(timezone.utc))
    out = GRAPH.invoke(s.model_dump() | {"last_user_message": user_message})
    return out

# (나중) Cloud Tasks가 7일 뒤 호출하는 엔드포인트
@app.post("/notify/weekly-nudge")
def weekly_nudge(payload: dict, x_internal_auth: str = Header(None)):
    from os import getenv
    if x_internal_auth != getenv("SERVICE_AUTH_HEADER", "dev-secret"):
        raise HTTPException(status_code=401, detail="unauthorized")
    # 개발 단계에선 그냥 OK
    return {"ok": True, "payload": payload}
