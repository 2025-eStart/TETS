from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List
from services.gpt_service import ask_gpt
from services.firebase_service import (
    save_chat_log,
    get_summaries_by_session,
    get_spending_by_date,
    add_spending_record,
)
from services.summary_service import save_summary
from services.game_service import (
    checkin_and_give_star,
    get_today,
    record_action,
    get_full_galaxy,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 채팅 요청 데이터 모델
class ChatRequest(BaseModel):
    message: str

# 🔹 요약 저장 요청 모델
class SummaryRequest(BaseModel):
    session_id: str
    emotion: str
    spending: str
    action: str

# 🔹 게임 행동 요청 모델
class ActionRequest(BaseModel):
    action_type: str  # ex: "counseling", "report", "breathing"

class SpendingRequest(BaseModel):
    session_id: str
    date: str  # "YYYY-MM-DD"
    spending: Dict[str, Any]

@app.get("/")
def hello():
    return {"message": "🎉 FastAPI 연결 성공!"}

# 🔸 GPT 챗봇 응답 API
@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        user_message = data.message
        gpt_response = ask_gpt(user_message)

        save_chat_log(
            session_id="test_session_1",  # TODO: 나중에 동적 세션 처리
            user_message=user_message,
            bot_response=gpt_response
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

# 🔸 요약 저장 API
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

# 🔸 요약 불러오기 API (GET)
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
# 🔸 게임 접속 보상 API
@app.post("/game/checkin")
def game_checkin():
    user_id = "test_user"  # TODO: 사용자 인증 후 변경
    today = get_today()
    result = checkin_and_give_star(user_id, today)

    return JSONResponse(content={
        "success": True,
        "message": "접속 보상 지급 완료!" if not result.get("already_checked_in") else "이미 오늘 보상 받음",
        "data": result
    })

@app.post("/game/action")
def game_action(data: ActionRequest):
    user_id = "test_user"
    today = get_today()

    result = record_action(user_id, today, data.action_type)

    if "error" in result:
        return JSONResponse(content={
            "success": False,
            "message": result["error"],
            "data": None
        })

    return JSONResponse(content={
        "success": True,
        "message": result["message"],
        "data": result["planets"]
    })

@app.get("/game/my-galaxy")
def get_my_galaxy(user_id: str = Query(...), month: str = Query(...)):
    try:
        galaxy_data = get_full_galaxy(user_id, month)
        return JSONResponse(content={
            "success": True,
            "message": "은하 정보 불러오기 성공!",
            "month": month,
            "galaxy": galaxy_data
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"에러 발생: {str(e)}",
            "data": None
        })
    
# 🔸 소비 내역 조회 API
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