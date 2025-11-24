# agent-server/src/main.py

'''
# FastAPI 서버로 LangGraph 그래프 실행

# 실행 명령 :
# uvicorn src.main:server --host 0.0.0.0 --port 8123 --reload

# 주요 기능:
    - API 1: 스레드 생성/유지; 유저 상태에 따라 적절한 스레드 ID와 세션 타입 생성 및 반환
    - API 2: 주어진 스레드 ID로 LangGraph 그래프 실행
    - API 3: 서랍 기능 (과거 채팅 내역 접근)

# 채팅 기능 요구사항: 세션 & 스레드(채팅방) 관리 규칙
    1. weekly session 을 수행한 지 만 일주일이 지난 후에야 다음 상담이 진행되도록 한다. 마지막 weekly 상담으로부터 아직 7일이 지나지 않았으면 채팅창에 접속하더라도 주간 상담이 진행되지 않는다.
    2. 주간 상담을 수행하다가 끝마치지 않음 && 24시간 이내 접속 →진행하던 데서부터 주간상담 진행 (즉, 기존과 같은 스레드)
    3. 주간 상담을 수행하다가 끝마치지 않음 && (24시간 이후 && 21일 미만) 접속 → 해당 주차 상담을 처음부터 다시 진행 (기존 주간상담 스레드 삭제 or end, 새로운 스레드 생성)
    4. 주간 상담을 수행했음 && 주간상담을 수행한 지 일주일 미만 →일반 FAQ (새로운 스레드)
    5. 주간 상담을 수행한 지 (일주일 이상&&21일 미만) → 마지막 상담 주차의 다음주차 주간상담 진행 (새로운 스레드)
    6. 미접속 21일 이상 → 주간 상담을 1주차부터 진행 (roll back, 새로운 스레드)
    7. 새로운 세션 만드는 버튼 UI(이걸 누르면 새로운 sessionType =="General" 세션이 생성되고, 새로운 thread가 시작됨. 단, 주간 상담 진행 중에는 새로운 세션을 만들 수 없고, ‘새로운 세션 만들기’ 버튼을 터치하면 ‘현재 진행 중인 주간 상담을 먼저 마무리해 주세요!’라는 안내문을 띄움
'''

import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# LangChain / LangGraph
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

# 내 프로젝트 모듈
from coach_agent.agent import app as graph_app  # 컴파일된 그래프
from coach_agent.services import REPO           # DB 접근용 (Firestore/Memory)
from coach_agent.utils._days_since import _days_since
from coach_agent.services.firestore_repo import _weekly_key # 주간 세션 키 생성용

# --- 앱 초기화 ---
server = FastAPI(title="CBT Coach Agent API")

# --- 데이터 모델 (DTO) ---
class InitSessionRequest(BaseModel):
    user_id: str
    force_new: bool = False  # "새로운 세션 만들기" 버튼 클릭 시 True

class InitSessionResponse(BaseModel):
    thread_id: str
    session_type: str        # "WEEKLY" | "GENERAL"
    display_message: str = "" # 화면에 띄울 안내 메시지
    current_week: int = 1    # 현재 주차 정보 추가

class ChatRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str
    session_type: str = "GENERAL" # 이건 기본값, 안드로이드가 init_session에서 받은 타입을 그대로 다시 보내줌

class ChatResponse(BaseModel):
    reply: str
    is_ended: bool
    current_week: int
    week_title: str
    week_goals: List[str]

class SessionSummary(BaseModel): # 서랍 기능
    session_id: str
    title: str       # 예: "1주차: 시작이 반이다" 또는 "일반 상담 (2025-11-24)"
    date: str        # 예: "2025-11-24"

# --- 헬퍼 함수 ---
def _get_active_thread_id(user_id: str, week: int) -> Optional[str]:
    """
    REPO에서 현재 주차의 활성 세션을 찾아서 thread_id(문서 ID)를 반환.
    없으면 None.
    """
    session = REPO.get_active_weekly_session(user_id, week)
    if session:
        # FirestoreRepo는 id 필드에 문서 ID를 담아줌
        return session.get("id")
    return None

# --- API 1: 세션 초기화 (교통정리) ---
@server.post("/session/init", response_model=InitSessionResponse)
async def init_session(req: InitSessionRequest):
    user_id = req.user_id
    now = datetime.now(timezone.utc)
    
    # 1. 유저 정보 조회
    user = REPO.get_user(user_id)
    last_seen = user.get("last_seen_at")
    last_completed = user.get("last_weekly_session_completed_at")
    current_week = int(user.get("current_week", 1))
    
    days_seen = _days_since(last_seen, now)
    days_completed = _days_since(last_completed, now)

    # 2. [요구사항 7] 강제 새 세션 (GENERAL)
    if req.force_new:
        return InitSessionResponse(
            thread_id=str(uuid.uuid4()), # 새 방
            session_type="GENERAL",
            display_message="새로운 일반 상담을 시작합니다.",
            current_week=current_week
        )

    # 3. [요구사항 6] 21일 이상 미접속 -> 롤백
    if days_seen >= 21:
        # DB 롤백 처리 (REPO 함수 재사용)
        REPO.rollback_user_to_week_1(user_id)
        # 롤백 후 1주차로 설정
        return InitSessionResponse(
            thread_id=str(uuid.uuid4()), # 새 방
            session_type="WEEKLY",
            display_message="오랜만에 오셨네요! 1주차부터 다시 시작합니다.",
            current_week=1
        )

    # 4. [요구사항 2, 3] 진행 중인 세션 확인
    active_thread_id = _get_active_thread_id(user_id, current_week)
    
    if active_thread_id:
        # 진행 중인 세션이 있음
        if days_seen < 1:
            # [요구사항 2] 24시간 이내 -> 기존 스레드 유지
            return InitSessionResponse(
                thread_id=active_thread_id,
                session_type="WEEKLY",
                current_week=current_week
            )
        else:
            # [요구사항 3] 24시간 경과 -> 재시작 (새 방)
            REPO.restart_current_week_session(user_id, current_week)
            return InitSessionResponse(
                thread_id=str(uuid.uuid4()), # 새 방
                session_type="WEEKLY",
                display_message="지난 상담이 오래되어 이번 주차를 처음부터 다시 시작합니다.",
                current_week=current_week
            )

    # 5. [요구사항 1, 4, 5] 진행 중인 세션 없음
    if last_completed and days_completed < 7:
        # [요구사항 1, 4] 쿨다운 기간 -> GENERAL
        return InitSessionResponse(
            thread_id=str(uuid.uuid4()),
            session_type="GENERAL",
            display_message="다음 주간 상담까지 대기 기간입니다. 자유롭게 대화하세요.",
            current_week=current_week
        )
    
    # [요구사항 5] 7일 지남 or 첫 시작 -> WEEKLY
    # (주차 진급은 채팅 시작 시 load_state나 route_session에서 처리되거나,
    #  여기서 미리 advance_to_next_week를 호출할 수도 있음.
    #  안전하게는 그래프 내부 로직에 맡기고 여기서는 안내만 함)
    
    # 만약 이미 완료된 주차라면 다음 주차로 진급시켜서 안내
    if last_completed:
        # (주의: advance_to_next_week는 DB를 업데이트하므로 신중하게 호출)
        # 여기서는 단순히 "다음 주차 상담 가능" 상태로 보고 WEEKLY 리턴
        pass

    return InitSessionResponse(
        thread_id=str(uuid.uuid4()),
        session_type="WEEKLY",
        display_message=f"{current_week}주차 상담을 시작합니다!",
        current_week=current_week
    )

# --- API 2: 채팅 (그래프 실행) ---
@server.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        # 1. LangGraph Config 설정
        # session_type은 init_session에서 결정되었지만, 
        # 그래프 내부 로직(route_session)이 한 번 더 검증할 것임.
        config = {
            "configurable": {
                "thread_id": req.thread_id,
                "user_id": req.user_id,                   # 안드로이드에서 보낸 device_id
                "session_type_override": req.session_type # WEEKLY/GENERAL 강제 지정
            }
        }
        
        # 2. 그래프 실행
        inputs = {"messages": [HumanMessage(content=req.message)]}
        
        # ainvoke로 비동기 실행
        final_state = await graph_app.ainvoke(inputs, config=config)

        # 3. 결과 파싱
        messages = final_state.get("messages", [])
        last_ai_msg = ""
        # 가장 마지막 AI 메시지 찾기 (역순 탐색)
        for msg in reversed(messages):
            if msg.type == "ai":
                last_ai_msg = msg.content
                break
        
        protocol = final_state.get("protocol") or {}
        
        return ChatResponse(
            reply=last_ai_msg,
            is_ended=final_state.get("exit", False),
            current_week=final_state.get("current_week", 1),
            week_title=protocol.get("title", "상담"),
            week_goals=protocol.get("goals", [])
        )

    except Exception as e:
        print(f"ERROR executing graph: {e}")
        # 상세 에러 로그 출력
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
# --- API 3: 서랍 (과거 채팅 내역 접근) ---
@server.get("/sessions/{user_id}", response_model=List[SessionSummary])
async def get_user_sessions(user_id: str):
    """
    유저의 모든 과거 세션 목록을 반환 (최신순)
    """
    # 1. DB에서 목록 가져오기
    sessions = REPO.get_all_sessions(user_id) 
    
    results = []
    for s in sessions:
        # --- [로직 1] ID 안전하게 가져오기 ---
        # Firestore 문서를 dict로 변환할 때 'id' 필드를 넣었겠지만, 
        # 혹시 몰라 'session_id' 필드도 확인하는 2중 안전장치
        sid = s.get("id") or s.get("session_id")
        if not sid: continue # ID가 없는 유령 데이터는 건너뜀

        # --- [로직 2] 날짜 예쁘게 변환하기 (YYYY-MM-DD) ---
        created_at = s.get("created_at")
        date_str = ""
        
        if isinstance(created_at, datetime):
            # datetime 객체라면 strftime으로 깔끔하게 변환 (가장 추천)
            date_str = created_at.strftime("%Y-%m-%d")
        elif created_at:
            # 문자열이거나 다른 타입이면 문자열 변환 후 앞부분만 자름
            date_str = str(created_at).split(" ")[0]
        else:
            # 날짜 정보가 없으면 오늘 날짜 혹은 "날짜 미상" 처리
            date_str = datetime.now().strftime("%Y-%m-%d")

        # --- [로직 3] 제목(Title) 결정 로직 ---
        # 1순위: DB에 이미 저장된 구체적인 제목이 있으면 그걸 씀 (예: "불안 다루기")
        # 2순위: 없으면 주차정보나 타입으로 생성
        if s.get("title"):
            display_title = s.get("title")
        else:
            week = s.get("week", 1)
            sType = s.get("session_type", "WEEKLY")
            
            if sType == "WEEKLY":
                display_title = f"{week}주차 상담"
            else:
                display_title = "자유 상담"

        # 결과 리스트에 추가
        results.append(SessionSummary(
            session_id=sid,
            title=display_title,
            date=date_str
        ))
        
    return results
