from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict

from services.gpt_service import ask_gpt
from services.firebase_service import (
    save_chat_log,
    get_summaries_by_session,
    get_spending_by_date,
    add_spending_record,
)
from services.summary_service import save_summary

app = FastAPI(title="TETS API")

# CORS (개발용 전체 허용; 배포 시 도메인 화이트리스트로 변경 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Schemas =====
class ChatRequest(BaseModel):
    message: str

class SummaryRequest(BaseModel):
    session_id: str
    emotion: str
    spending: str
    action: str

class SpendingRequest(BaseModel):
    session_id: str           # "test_session_1" 등
    date: str                 # "YYYY-MM-DD"
    spending: Dict[str, Any]  # {title, amount, method, is_impulse, ...}

# ===== Health / Root =====
@app.get("/")
def hello():
    return {"message": "🎉 FastAPI 연결 성공!"}

# ===== Chat =====
@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        user_message = data.message
        gpt_response = ask_gpt(user_message)

        # TODO: session_id 동적 처리 (임시 하드코딩)
        save_chat_log(
            session_id="test_session_1",
            user_message=user_message,
            bot_response=gpt_response,
        )

        return JSONResponse(content={
            "success": True,
            "message": "GPT 응답 성공!",
            "data": gpt_response
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"GPT 응답 실패: {str(e)}",
            "data": None
        })

# ===== Summaries =====
@app.post("/save-summary")
def save_summary_api(data: SummaryRequest):
    try:
        result = save_summary(data.session_id, data.dict(exclude={"session_id"}))
        return JSONResponse(content={
            "success": True,
            "message": "요약 저장 완료!",
            "data": result
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"요약 저장 실패: {str(e)}",
            "data": None
        })

@app.get("/get-reports")
def get_reports(session_id: str = Query(..., description="세션 ID")):
    try:
        reports = get_summaries_by_session(session_id)
        return JSONResponse(content={
            "success": True,
            "message": "요약 조회 성공!",
            "data": reports
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"요약 조회 실패: {str(e)}",
            "data": None
        })

# ===== Transactions (Spending) =====
@app.get("/spending-history")
def get_spending_history(
    session_id: str = Query(..., description="세션 ID"),
    date: str = Query(..., description="형식: YYYY-MM-DD")
):
    try:
        data = get_spending_by_date(session_id, date)
        return JSONResponse(content={
            "success": True,
            "message": "소비 내역 조회 성공!",
            "data": data
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"조회 실패: {str(e)}",
            "data": None
        })

@app.post("/save-spending")
def save_spending(data: SpendingRequest):
    try:
        add_spending_record(data.session_id, data.date, data.spending)
        return JSONResponse(content={
            "success": True,
            "message": "소비 내역 저장 성공!"
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"소비 내역 저장 실패: {str(e)}"
        })