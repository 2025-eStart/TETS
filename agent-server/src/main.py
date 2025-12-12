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
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# LangChain / LangGraph
from langchain_core.messages import HumanMessage

# 내 프로젝트 모듈
from coach_agent.graph import app as graph_app  # 컴파일된 그래프
from coach_agent.services import REPO           # DB 접근용 (Firestore/Memory)
from coach_agent.utils._days_since import _days_since

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
    is_weekly_in_progress: bool = False # 주간 상담이 진행 중인지 여부; 새로운 세션 생성 버튼 비활성화 여부 결정
    created_at: str = ""     # 생성 시각 (ISO 문자열); ui 상단 바 출력용
    status: str = "active"

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
    
# 과거 메시지 하나 (Response) (서랍용)
class MessageHistoryItem(BaseModel):
    role: str       # "human" | "ai"
    text: str
    created_at: Optional[datetime] = None

class SessionSummary(BaseModel): # 서랍 기능
    session_id: str
    title: str       # 예: "1주차: 시작이 반이다" 또는 "일반 상담 (2025-11-24)"
    date: str        # 예: "2025-11-24"
    session_type: str
    status: Optional[str] = None  # "active", "ended" 등

# --- 헬퍼 함수 ---
# init_session: 활성 세션 조회 헬퍼 함수
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

# init_session: 시간 포맷팅 헬퍼 함수 (서랍 목록과 형식 통일: YY-MM-DD HH:MM)
def _format_kst(dt_obj: datetime) -> str:
    if not dt_obj:
        return ""
    # UTC -> KST 변환
    KST = timezone(timedelta(hours=9))
    if dt_obj.tzinfo is None:
        # naive datetime이면 UTC라고 가정
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    
    return dt_obj.astimezone(KST).strftime("%y-%m-%d %H:%M")

# --- API 1: 세션 초기화 (교통정리) ---
@server.post("/session/init", response_model=InitSessionResponse)
async def init_session(req: InitSessionRequest):
    '''
    역할: 클라이언트가 앱을 켤 때마다(혹은 채팅방에 들어갈 때마다) 가장 먼저 호출하는 "안내 데스크"
    1. "방 번호 안내" (라우팅): 유저의 상태(마지막 접속일, 주차 등)를 보고 thread_id(방 번호)와 session_type(상담 종류)을 결정해 반환한다.
    2. "방 명패 달기" (세션 타입 박제): 만약 새 방을 배정해줬다면, DB에 미리 "이 방은 WEEKLY 방입니다"라고 기록(save_session_info)해둔다.
    '''
    
    # 디버깅 출력--------------------------------
    print(f"\n🚀 [API Debug] /session/init 요청 도착: User={req.user_id}, Force={req.force_new}")
    # ----------------------------------------
    user_id = req.user_id
    now = datetime.now(timezone.utc)
    
    # 1. 유저 정보 조회
    user = REPO.get_user(user_id)
    last_seen = user.get("last_seen_at")
    last_completed = user.get("last_weekly_session_completed_at")
    current_week = int(user.get("current_week", 1))
    
    days_seen = _days_since(last_seen, now)
    days_completed = _days_since(last_completed, now)
    
    # 디버깅 출력--------------------------------
    print(f"   - [API Debug] User Info: Week={current_week}")
    print(f"""   - [API Debug] Days Since Last Seen(days_seen): now - last_seen
                                                    = '{now}' - '{last_seen}'
                                                    = {days_seen}
        """)
    print(f"""   - [API Debug] Days Since Last Completed(days_completed): now - last_completed
                                                                = '{now}' - '{last_completed}'
                                                                = {days_completed}
          """)
    print(f"   - [API Debug] Force New Session 체크(force_new): {req.force_new}") # 디버깅
    # ----------------------------------------
    
    '''
    [1] response_data 변수 설명:
    - 리턴할 InitSessionResponse 객체 임시 저장
    
    [2] session_created_at_dt 변수 설명:
    - DB 저장 및 응답에 사용할 세션 생성 시간
    - 새 세션인 경우 -> now 사용
    - 기존 세션인 경우 -> DB에서 가져온 값 사용
    '''
    response_data = None
    session_created_at_dt = now
    
    # 2. [요구사항 7] 강제 새 세션 (GENERAL)
    if req.force_new:
        print("   - [API Debug] 강제 새 세션 요청 -> GENERAL 세션 생성") # 디버깅
        response_data = InitSessionResponse(
            thread_id=str(uuid.uuid4()), # 새 방
            session_type="GENERAL",
            display_message="새로운 일반 상담을 시작합니다.",
            current_week=current_week,
            status="active"
        )
        session_created_at_dt = now # 새 주간 상담 세션이므로 현재 시각

    # 3. [요구사항 6] 21일 이상 미접속 -> 롤백
    elif days_seen >= 21:
        print("   - [API Debug] 21일 이상 미접속 -> 1주차로 롤백") # 디버깅
        # DB 롤백 처리 (REPO 함수 재사용)
        REPO.rollback_user_to_week_1(user_id)
        # 롤백 후 1주차로 설정
        response_data = InitSessionResponse(
            thread_id=str(uuid.uuid4()), # 새 방
            session_type="WEEKLY",
            display_message="오랜만에 오셨네요! 1주차부터 다시 시작합니다.",
            current_week=1,
            status="active"
        )
        session_created_at_dt = now # 새 주간 상담 세션이므로 현재 시각
        
    # [요구사항 1, 4] 쿨다운 기간 -> GENERAL
    elif days_completed < 7:
        print("   - [API Debug] 쿨다운 기간(7일 미만) -> GENERAL 세션 생성") # 디버깅
        response_data = InitSessionResponse(
            thread_id=str(uuid.uuid4()),
            session_type="GENERAL",
            display_message="다음 주간 상담까지 대기 기간입니다. 자유롭게 대화하세요.",
            current_week=current_week,
            status="active"
        )
        session_created_at_dt = now # 새 일반 상담 세션이므로 현재 시각
        
    # 4. [요구사항 2, 3] 진행 중인 세션 확인: 쿨다운 기간이 아니고, 강제 새 세션도 아니면
    else:
        print("   - [API Debug] 쿨다운 기간 아님 -> 진행 중인 세션 확인...") # 디버깅
        print("   - [API Debug] Active 세션 검색 시도...") # 디버깅
        
        active_session = REPO.get_active_weekly_session(user_id, current_week)
        print(f"   - [API Debug] 검색 결과 ID: {active_session}") # 디버깅
    
        if active_session:
            # 진행 중인 세션이 있음
            if days_seen < 1:
                # [요구사항 2] 24시간 이내 -> 기존 스레드 유지
                current_status = active_session.get("status", "active")
                response_data = InitSessionResponse(
                    thread_id=active_session["id"],
                    session_type="WEEKLY",
                    current_week=current_week,
                    status=current_status
                )
                print("   - [API Debug] 기존 세션 유지 선택") # 디버깅
                # 기존 세션이므로 DB에 있는 created_at을 가져옴
                # (Firestore Timestamp -> datetime 변환은 repo가 해줌)
                if "created_at" in active_session:
                    session_created_at_dt = active_session["created_at"]
            else:
                # [요구사항 3] 24시간 경과 -> 재시작 (새 방)
                REPO.restart_current_week_session(user_id, current_week)
                new_id = str(uuid.uuid4())
                print(f"   - [API Debug] 새로운 방에서 이번 주차 상담 재시작: {new_id}") # 디버깅
                
                response_data = InitSessionResponse(
                    thread_id=new_id, # 새 스레드(채팅방)
                    session_type="WEEKLY",
                    display_message="지난 상담이 오래되어 이번 주차를 처음부터 다시 시작합니다.",
                    current_week=current_week,
                    status="active"
                )
                session_created_at_dt = now # 새 주간 상담 세션이므로 현재 시각
    
        # [요구사항 5] 7일 지남 or 첫 시작(신규사용자) -> WEEKLY
        # 완료 표시 및 주차 진급은 상담 완료 후 메인 그래프의 update_progress 노드의 mark_session_as_completed 함수에서 처리
        else:
            if last_completed:
                # [상황 A] 지난 주차를 완료하고 7일이 지난 유저
                # (다음 주차 진급이 지난 주차 상담 완료 시 update_progress에서 처리되므로 여기서는 current_week가 이미 진급되어 있음)
                # 여기서는 단순히 "다음 주차 상담 가능" 상태로 보고 WEEKLY 리턴
                print("   - [API Debug] Active 세션 없음 -> 새로운 WEEKLY 세션 생성 결정")
            
                # [추가 디버깅] 왜 없다고 판단했는지 확인하기 위해 여기서 바로 만들어지는 ID 출력
                new_id = str(uuid.uuid4())
                print(f"   - [API Debug] 새로 발급된 ID: {new_id}")
                
                response_data = InitSessionResponse(
                    thread_id=new_id,
                    session_type="WEEKLY",
                    # display_message=f"{current_week}주차 상담을 시작합니다!", #weekly graph의 greeting node에서 수행됨
                    current_week=current_week,
                    status="active"
                )
                session_created_at_dt = now
            else:
                # [상황 B] 신규 유저 (1주차)
                response_data = InitSessionResponse(
                    thread_id=str(uuid.uuid4()),
                    session_type="WEEKLY",
                    # display_message="충동 소비 상담소에 오신 것을 환영합니다! 1주차 상담을 시작할게요.", #weekly graph의 greeting node에서 수행됨
                    current_week=1,
                    status="active"
                )
                session_created_at_dt = now

    # -------------------------------------------------------
    # 1. 주간상담 진행 시 '새 세션 생성' 버튼 비활성화하도록 플래그 설정
    # 2. thread id가 발급되는 즉시 바로 DB에 세션 정보를 저장 -> 같은 세션이 다른 스레드로 분리되는 현상 방지
    # -------------------------------------------------------
    if response_data:
        # --------1. 주간상담 진행 시 '새 세션 생성' 버튼 비활성화하도록 플래그 설정----------
        # 세션 타입이 'WEEKLY'라면 -> 현재 주간 상담 진행 중 -> 버튼 비활성화(True)
        if response_data.session_type == "WEEKLY":
            response_data.is_weekly_in_progress = True
        else:
            # 'GENERAL' 이라면 -> 자유 대화 기간 -> 버튼 활성화(False)
            response_data.is_weekly_in_progress = False
        
        # 클라이언트에게 보낼 날짜 포맷팅 (KST 변환)
        response_data.created_at = _format_kst(session_created_at_dt)
        
        try:
            # ----- 2. 새로 생성된 thread id라면, 바로 DB에 세션 정보 저장 / 아니라면 last_activity_at 갱신 -----
            print(f"   - [API Debug] thread id 발급 직후 바로 DB에 저장: ID={response_data.thread_id}")
            REPO.save_session_info(
                user_id=user_id,
                thread_id=response_data.thread_id, # [중요] 스레드 ID 명시
                session_type=response_data.session_type,# [중요] 타입 강제 지정
                week=response_data.current_week,
                created_at=session_created_at_dt, # 생성 시각 명시
            )

                
        except Exception as e:
            print(f"Warning: Failed to save session info after create thread id: {e}")
            # 여기서 에러가 나도 클라이언트에게는 일단 응답을 보내줌
            pass

    return response_data

# --- API 2: 채팅 (그래프 실행) ---
@server.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    print(f"\n🔥 [Chat API Start] Thread={req.thread_id}, UserMsg='{req.message}', SessionType={req.session_type}") # 디버깅
    try:
        # 1. 그래프 입력값(Inputs) 준비
        inputs = {
            "messages": [HumanMessage(content=req.message)],
        }
        # 2. LangGraph Config 설정
        config = {
            "configurable": {
                "thread_id": req.thread_id,
                "user_id": req.user_id,                   # 안드로이드에서 보낸 device_id
                "session_type_override": req.session_type # WEEKLY/GENERAL 강제 지정
            }
        }
        
        print(f"   -> [Graph Invoke] Config: {config['configurable']}") # 디버깅
        
        # 3. ainvoke로 그래프 비동기 실행
        final_state = await graph_app.ainvoke(inputs, config=config)
        is_ended = final_state.get("exit", False) # 그래프 결과에서 종료 여부 추출

        # ---- 디버깅: 메시지 개수 및 마지막 메시지 내용 출력 ----
        print("   -> [Graph Finished] Final State Keys:", final_state.keys())
        msgs = final_state.get("messages", [])
        print(f"   -> [Graph Messages Count]: {len(msgs)}") 
        if msgs:
            print(f"   -> [Last Message]: Type={msgs[-1].type}, Content='{msgs[-1].content}'")
        # ----------------------------------------------------

        # 4. 결과 파싱
        messages = final_state.get("messages", [])
        last_ai_msg = ""
        
        # 역순 탐색하되, 시스템 메시지나 __init__은 무시
        for msg in reversed(msgs):
            if msg.type == "ai":
                content = msg.content
                
                # 내용 추출 (리스트/문자열 처리)
                if isinstance(content, list):
                    temp_text = "\n\n".join([str(c) for c in content if isinstance(c, str)])
                else:
                    temp_text = str(content)
                
                # 유효성 검사 (__init__ 제외, 빈 문자열 제외)
                if temp_text and temp_text.strip() and temp_text.strip() != "__init__":
                    last_ai_msg = temp_text
                    break
        
        if not last_ai_msg:
            last_ai_msg = "(응답 없음)"
        
        print(f"   -> [Parsed AI Reply]: '{last_ai_msg}'") # 디버깅
        
        # 만약 메시지가 비어있다면 디버깅용 메시지
        if not last_ai_msg:
            last_ai_msg = "(응답 없음)"
            
        # 5. DB 저장 로직 (그래프 정상 실행 시에만)
        current_week = final_state.get("current_week", 1)

        # __init__ message는 저장하지 않기
        # 5-1. user 메시지 저장
        user_text = req.message or ""
        if user_text.strip() != "__init__":
            REPO.save_message(
                user_id=req.user_id,
                thread_id=req.thread_id,
                session_type=req.session_type,
                week=current_week,
                role="user",
                text=user_text,
            )

        # 5-2. AI 메시지 저장
        if last_ai_msg and last_ai_msg != "(응답 없음)":
            REPO.save_message(
                user_id=req.user_id,
                thread_id=req.thread_id,
                session_type=req.session_type,
                week=current_week,
                role="assistant",
                text=last_ai_msg,
            )

        # 6. 응답 구성
        week_title = final_state.get("agenda") or "상담" 
        raw_criteria = final_state.get("success_criteria") or []
        week_goals = [
            c.get("description") or c.get("label") or c.get("id", "")
            for c in raw_criteria
            if isinstance(c, dict)
        ]
        
        return ChatResponse(
            reply=last_ai_msg,
            is_ended=is_ended,
            current_week=current_week,
            week_title=week_title,
            week_goals=week_goals,
        )

    except Exception as e:
        print(f"ERROR executing graph: {e}")
        import traceback
        traceback.print_exc()
        # ❗ 여기서는 save_message를 전혀 호출하지 않았으므로
        #    이번 턴의 user/assistant 아무것도 DB에 남지 않음.
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
        # --- ID 안전하게 가져오기 ---
        sid = s.get("id") or s.get("session_id")
        if not sid: continue # ID가 없는 유령 데이터는 건너뜀

        # --- 미완료&&종료 세션 서랍에서 숨기기 ---
        # 'result'가 'abandoned'인 세션은 서랍 목록에서 숨김(건너뛰기)
        if s.get("result") == "abandoned": continue
        session_status = s.get("status")
        
        # --- 날짜 예쁘게 변환하기 (YY-MM-DD HH:MM) ---
        created_at = s.get("created_at")
        date_str = ""
        
        # 1. Firebase Timestamp 객체라면 datetime으로 변환
        if hasattr(created_at, 'to_datetime'):
            created_at = created_at.to_datetime()

        # 2. datetime 객체인지 확인 후 포맷팅
        if isinstance(created_at, datetime):
            # Firebase에는 UTC로 저장되므로 한국 시간(KST)으로 변환
            if created_at.tzinfo:
                KST = timezone(timedelta(hours=9))
                created_at = created_at.astimezone(KST)
            
            # 원하는 포맷: 25-12-11 16:44
            date_str = created_at.strftime("%y-%m-%d %H:%M")

        elif created_at:
            # 만약 문자열로 저장된 경우라면 (예외 처리)
            # 단순히 잘라서 보여주거나, 위의 파싱 로직 사용
            date_str = str(created_at)[:16] 

        else:
            # 날짜 정보가 없을 때: 현재 시간(KST) 기준
            KST = timezone(timedelta(hours=9))
            date_str = datetime.now(KST).strftime("%y-%m-%d %H:%M")

        # --- 제목(Title) 결정 로직 ---
        # 상담 세션: {week}주차 상담 | {날짜}
        # 일반 세션: FAQ | {날짜}
        # 1순위: DB에 이미 저장된 구체적인 제목이 있으면 그걸 씀 (예: "불안 다루기")
        # 2순위: 없으면 주차정보나 타입으로 생성
        s_type = s.get("session_type", "GENERAL") 
        week = s.get("week")
        if s_type and week and date_str:
            if s_type == "WEEKLY":
                display_title = f"{week}주차 상담 | {date_str}"
            else:
                display_title = f"FAQ | {date_str}"
        else:
            if s_type == "WEEKLY":
                display_title = f"상담 | {date_str}"
            else:
                display_title = f"FAQ | {date_str}"

        # 결과 리스트에 추가
        results.append(SessionSummary(
            session_id=sid,
            title=display_title,
            date=date_str,
            session_type=s_type,
            status=session_status
        ))
        
    return results

# --- API 4: 서랍 상세: 특정 세션의 대화 내용 가져오기 ---
@server.get("/history/{user_id}/{thread_id}", response_model=List[MessageHistoryItem])
async def get_session_history(user_id: str, thread_id: str):
    """
    특정 스레드(세션)의 모든 대화 내용을 시간순으로 반환
    (단, 시스템 초기화 메시지 '__init__'은 제외하고 반환하여 클라이언트가 첫 시작임을 알게 함)
    """
    messages = REPO.get_session_messages(user_id, thread_id)
    
    # [수정] 필터링 로직 추가
    filtered_messages = []
    for msg in messages:
        text = msg.get("text", "")
        role = msg.get("role", "")
        
        # 1. 텍스트가 '__init__'인 경우 제외
        # (DB 저장 시 양옆 공백이 들어갔을 수도 있으니 strip() 권장)
        if text and text.strip() == "__init__":
            continue
            
        # 2. role이 'system'인 경우 제외 (화면에 뿌릴 필요 없음)
        if role == "system":
            continue
            
        filtered_messages.append(msg)
        
    return filtered_messages