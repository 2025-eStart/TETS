from typing import Optional

from fastapi import FastAPI, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.firebase_service import admin_get_raw_state, upsert_assignment
from services.gpt_service import ask_gpt
from services.firebase_service import (
    # 기존 사용
    save_chat_log,
    save_summary,
    get_summaries_by_session,
    get_spending_by_date,
    add_spending_record,
    get_counseling_detail,
    # 추가 라우트에서 사용할 것들
    start_session,
    append_message,
    update_session_state,
    end_session,
    get_active_session,
    create_practice_log,
    query_practice_logs,
    get_daily_dashboard,
    get_weekly_dashboard,
    admin_get_raw_state, start_session, append_message,
    update_session_state, end_session, get_active_session, upsert_assignment
)
from settings import DEMO_MODE, SESSION_MAX_TURNS
from services.protocol import STEP_FLOW, WEEK_SCRIPT
from services.gpt_service import ask_protocol_driven

app = FastAPI(title="TETS API")

# ===== CORS (개발용 전체 허용; 배포 시 화이트리스트 권장) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 화이트리스트로 교체 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Models =====
class ChatRequest(BaseModel):
    uid: str = Field(..., description="Firebase UID")
    session_id: str
    message: str

class SummaryRequest(BaseModel):
    uid: str
    session_id: str
    emotion: str
    spending: str
    action: str

class SpendingRecord(BaseModel):
    uid: str
    date: str  # YYYY-MM-DD
    title: str
    amount: int
    method: str
    is_impulse: bool
    counseling_id: Optional[str] = None

# ===== Routes (기존) =====
@app.get("/")
def hello():
    return {"message": "🎉 FastAPI 연결 성공!"}

@app.post("/chat")
def chat(data: ChatRequest):
    try:
        gpt_result = ask_gpt(data.message)

        # summaries/{id} 생성 + id 반환
        summary_saved = save_summary(
            uid=data.uid,
            session_id=data.session_id,
            summary_data={
                "emotion": gpt_result.get("emotion"),
                "spending": gpt_result.get("spending"),
                "action": gpt_result.get("action"),
            },
        )

        # 채팅 로그 저장
        save_chat_log(
            uid=data.uid,
            session_id=data.session_id,
            user_message=data.message,
            bot_response=gpt_result,
        )

        return JSONResponse(
            content=jsonable_encoder(
                {
                    "success": True,
                    "message": "GPT 응답 및 요약 저장 성공!",
                    "data": {
                        "counseling_id": summary_saved["counseling_id"],
                        **gpt_result,
                    },
                }
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {
                    "success": False,
                    "message": f"GPT/요약 처리 실패: {str(e)}",
                    "data": None,
                }
            )
        )

@app.post("/save-summary")
def save_summary_api(data: SummaryRequest):
    try:
        result = save_summary(
            uid=data.uid,
            session_id=data.session_id,
            summary_data=data.model_dump(exclude={"uid", "session_id"}),
        )
        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "message": "요약 저장 완료!", "data": result}
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {"success": False, "message": "요약 저장 실패: " + str(e), "data": None}
            )
        )

@app.get("/get-reports")
def get_reports(uid: str = Query(...), session_id: str = Query(...)):
    try:
        reports = get_summaries_by_session(uid, session_id)
        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "message": "요약 조회 성공!", "data": reports}
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {"success": False, "message": "요약 조회 실패: " + str(e), "data": None}
            )
        )

@app.post("/save-spending")
def save_spending(data: SpendingRecord):
    try:
        add_spending_record(data.uid, data.model_dump())
        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "message": "소비 내역 저장 성공!"}
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {"success": False, "message": "소비 내역 저장 실패: " + str(e)}
            )
        )

@app.get("/spending-history")
def spending_history(
    uid: str = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    include_counseling_id: bool = Query(False),
):
    try:
        data = get_spending_by_date(uid, date, include_counseling_id)
        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "message": "소비 내역 조회 성공!", "data": data}
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {"success": False, "message": "조회 실패: " + str(e), "data": None}
            )
        )

@app.get("/counseling-detail")
def counseling_detail(
    uid: str = Query(...),
    session_id: str = Query(...),
    counseling_id: str = Query(...),
):
    try:
        data = get_counseling_detail(uid, session_id, counseling_id.strip())
        if not data:
            return JSONResponse(
                content=jsonable_encoder(
                    {"success": False, "message": "상담 내용 없음", "data": None}
                )
            )
        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "message": "상담 내용 조회 성공!", "data": data}
            )
        )
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder(
                {"success": False, "message": "상담 조회 실패: " + str(e), "data": None}
            )
        )

# ===== Routes (추가 · 6개 묶음 + 리포트) =====
# 1) 주간 세션 시작/재개
@app.post("/chat/session/start")
def api_session_start(
    uid: str = Query(..., description="Firebase UID"),
    week: int = Query(..., ge=1, le=10),
    resume: bool = Query(False),
):
    """
    예) POST /chat/session/start?uid=U123&week=3&resume=true
    """
    try:
        data = start_session(uid, week, resume)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# 2) 세션 내 메시지 (MVP: 상태 미사용 → 추후 state-aware로 개선)
@app.post("/chat/session/{session_id}/message")
def api_session_message(
    session_id: str,
    uid: str = Query(..., description="Firebase UID"),
    text: str = Query(..., description="사용자 입력 텍스트"),
    step_hint: Optional[str] = Query(None),
):
    """
    예) POST /chat/session/abcd123/message?uid=U123&text=오늘+지출+걱정돼&step_hint=w3_intro
    """
    try:
        # 1) 사용자 메시지 기록
        append_message(uid, session_id, role="user", text=text, step_key=step_hint)

        # 2) (MVP) 현재 state 미사용 LLM 호출
        reply_obj = ask_gpt(text)  # {emotion, spending, action}

        # 3) 어시스턴트 메시지 기록 + 상태 업데이트(placeholder)
        append_message(uid, session_id, role="assistant", text=str(reply_obj), step_key="wX_step_reply")
        update_session_state(uid, session_id, state={"next": "todo"}, step_key="wX_step_reply")

        return JSONResponse(
            content=jsonable_encoder(
                {"reply": reply_obj, "state": {"next": "todo"}, "step_key": "wX_step_reply"}
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# 3) 세션 종료
@app.post("/chat/session/{session_id}/end")
def api_session_end(
    session_id: str,
    uid: str = Query(..., description="Firebase UID"),
    reason: Optional[str] = Query(None),
):
    """
    예) POST /chat/session/abcd123/end?uid=U123&reason=user_done
    """
    try:
        data = end_session(uid, session_id, reason)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# 4) 현재 활성 세션 조회
@app.get("/chat/session/active")
def api_session_active(uid: str = Query(..., description="Firebase UID")):
    """
    예) GET /chat/session/active?uid=U123
    """
    try:
        data = get_active_session(uid)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# 5) 실습 로그 작성
@app.post("/practice/logs")
def api_create_practice_log(
    body: dict,
    uid: str = Query(..., description="Firebase UID"),
):
    """
    body 예:
    {
      "date": "2025-10-21",
      "assignment_id": "asgn_abc123",
      "adherence": 80,
      "obstacles": ["늦은 공부 일정"],
      "mood": 3,
      "urge": 4,
      "notes": "메모"
    }
    """
    try:
        data = create_practice_log(uid, body)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# 6) 실습 로그 조회(+간단 통계)
@app.get("/practice/logs")
def api_query_practice_logs(
    uid: str = Query(..., description="Firebase UID"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """
    예) GET /practice/logs?uid=U123&date_from=2025-10-01&date_to=2025-10-31
    """
    try:
        data = query_practice_logs(uid, date_from, date_to)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# (리포트) 일간 대시보드
@app.get("/dashboard/daily")
def api_daily(
    uid: str = Query(..., description="Firebase UID"),
    date: str = Query(..., description="YYYY-MM-DD"),
):
    """
    예) GET /dashboard/daily?uid=U123&date=2025-10-21
    """
    try:
        data = get_daily_dashboard(uid, date)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )

# (리포트) 주간 대시보드
@app.get("/dashboard/weekly")
def api_weekly(
    uid: str = Query(..., description="Firebase UID"),
    week_idx: int = Query(..., ge=1, le=10),
):
    """
    예) GET /dashboard/weekly?uid=U123&week_idx=3
    """
    try:
        data = get_weekly_dashboard(uid, week_idx)
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": str(e)})
        )
# --- 단일 파사드 엔드포인트: /chat/next ---
from fastapi import Body
from services.firebase_service import (
    get_active_session, start_session, append_message,
    update_session_state, end_session,
)

class ChatNextReq(BaseModel):
    uid: str
    text: str = ""
    week: Optional[int] = Field(default=None, description="없으면 서버가 자동 세션 시작")
    step_hint: Optional[str] = None  # 데모에선 미사용
    end: bool = Field(default=False, description="이 호출로 세션 마무리할지")

class ChatNextResp(BaseModel):
    session_id: str
    reply: dict
    state: dict
    is_ended: bool
    panel_updates: Optional[dict] = None
    homework: Optional[dict] = None


@app.post("/chat/next", response_model=ChatNextResp)
def chat_next(payload: ChatNextReq):
    uid = payload.uid

    # 1) 세션 확보 (없으면 새로 시작)
    active = get_active_session(uid) or {}
    session_id = active.get("session_id")
    if not session_id:
        week = payload.week or 1
        session = start_session(uid, week=week, resume=False)
        session_id = session["session_id"]

    # 2) 상태 로드/초기화
    raw = admin_get_raw_state(uid, session_id) or {}
    state = raw.get("state") or {}
    if "index" not in state:
        state["week"] = state.get("week") or (payload.week or active.get("week") or 1)
        state["index"] = 0
        state["step"] = STEP_FLOW[state["index"]]  # 보통 "intro"
        state["turns"] = 0
        state["progress"] = round((state["index"] + 1) / len(STEP_FLOW), 2)

    week = state["week"]
    step = state["step"]
    user_text = (payload.text or "").strip()

    # ========== (A) 첫 진입: 사용자 입력이 없을 때 챗봇이 먼저 말 걸기 ==========
    if not user_text and state.get("turns", 0) == 0:
        reply_obj = ask_protocol_driven(week=week, step=step, user_text="", history=[])

        append_message(uid, session_id, role="assistant",
                       text=reply_obj.get("text", ""), step_key=step)
        update_session_state(uid, session_id, state=state, step_key=step)

        return ChatNextResp(
            session_id=session_id,
            reply=reply_obj,
            state=state,
            is_ended=False,
            panel_updates=None,
            homework=None,
        )

    # ========== (B) 빈 입력 방어: 챗봇이 부드럽게 리드하고 종료 ==========
    if not user_text:
        reply_obj = ask_protocol_driven(week=week, step=step, user_text="", history=[])
        append_message(uid, session_id, role="assistant",
                       text=reply_obj.get("text", ""), step_key=step)
        update_session_state(uid, session_id, state=state, step_key=step)

        return ChatNextResp(
            session_id=session_id,
            reply=reply_obj,
            state=state,
            is_ended=False,
            panel_updates=None,
            homework=None,
        )

    # ========== (C) 정상 입력 흐름 ==========
    # 3) 사용자 메시지 기록
    append_message(uid, session_id, role="user", text=user_text, step_key=step)

    # 4) LLM 호출
    reply_obj = ask_protocol_driven(week=week, step=step,
                                    user_text=user_text, history=[])

    # 5) 다음 단계 계산 (최대 한 단계만 전진, 건너뛰기 금지)
    current_idx = state["index"]
    suggested = reply_obj.get("next_step")

    if suggested in STEP_FLOW:
        sugg_idx = STEP_FLOW.index(suggested)
    else:
        sugg_idx = current_idx + 1

    allowed_next_idx = min(current_idx + 1, len(STEP_FLOW) - 1)
    next_idx = sugg_idx if sugg_idx <= allowed_next_idx else allowed_next_idx

    # skill_training 이전에는 homework/summary 금지 (안전 가드)
    i_skill = STEP_FLOW.index("skill_training") if "skill_training" in STEP_FLOW else len(STEP_FLOW) - 1
    if next_idx >= STEP_FLOW.index("homework") and current_idx < i_skill:
        next_idx = allowed_next_idx

    next_step = STEP_FLOW[next_idx]
    state.update({
        "index": next_idx,
        "step": next_step,
        "turns": state.get("turns", 0) + 1,
        "progress": round((next_idx + 1) / len(STEP_FLOW), 2),
    })

    # 6) 어시스턴트 메시지 기록 + 상태 저장 (텍스트만!)
    append_message(uid, session_id, role="assistant",
                   text=reply_obj.get("text", ""), step_key=step)
    update_session_state(uid, session_id, state=state, step_key=step)

    # 7) 종료 요건
    is_ended = False
    homework = None
    reached_summary = (state["step"] == "summary")
    turns_over = (state["turns"] >= SESSION_MAX_TURNS)

    if payload.end or reached_summary or turns_over:
        is_ended = True
        hw_list = WEEK_SCRIPT.get(week, {}).get("homework", {}).get("homework", [])
        homework = {
            "week": week,
            "title": f"{week}주차 과제",
            "instructions": " / ".join(hw_list) if hw_list else "이번 주 자유 기록 1줄",
        }
        try:
            upsert_assignment(uid, session_id, homework)
        except Exception:
            pass
        end_session(uid, session_id, reason="demo_end")

    return ChatNextResp(
        session_id=session_id,
        reply=reply_obj,
        state=state,
        is_ended=is_ended,
        panel_updates=None,
        homework=homework,
    )