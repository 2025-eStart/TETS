# services/firebase_service.py
from __future__ import annotations
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Literal, Iterable, Set
from collections import defaultdict

import firebase_admin
from firebase_admin import credentials, firestore
from google.api_core.exceptions import FailedPrecondition, NotFound

# ------------------------------------------------------------------------------
# Firebase Admin 초기화
# ------------------------------------------------------------------------------
if not firebase_admin._apps:
    # 서비스 계정 키가 없으면 ADC(Application Default Credentials) 사용
    cred: credentials.Base = None
    try:
        key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json")
        cred = credentials.Certificate(key_path) if os.path.exists(key_path) else credentials.ApplicationDefault()
    except Exception:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ------------------------------------------------------------------------------
# 유틸
# ------------------------------------------------------------------------------
def _to_iso(ts: Any) -> Optional[str]:
    """Firestore Timestamp -> ISO8601 문자열 변환 (없으면 None)"""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.isoformat()
    # firebase_admin.firestore.Timestamp 타입도 datetime 호환
    try:
        return ts.isoformat()
    except Exception:
        return None

def _safe_order(collection_ref: firestore.CollectionReference, field: str, direction=firestore.Query.ASCENDING):
    """
    인덱스 미설정 등으로 order_by가 실패할 때를 대비한 안전 wrapper.
    """
    try:
        return collection_ref.order_by(field, direction=direction).stream()
    except FailedPrecondition:
        return collection_ref.stream()

def _required(v, name: str):
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError(f"{name} is required")
    return v

# ------------------------------------------------------------------------------
# [공통] Users 루트 및 하위 컬렉션 Path Helper
# users/{uid}/sessions/{session_id}/...
# ------------------------------------------------------------------------------
def _user_doc(uid: str) -> firestore.DocumentReference:
    return db.collection("users").document(uid)

def _sessions_col(uid: str) -> firestore.CollectionReference:
    return _user_doc(uid).collection("sessions")

def _session_doc(uid: str, session_id: str) -> firestore.DocumentReference:
    return _sessions_col(uid).document(session_id)

def _messages_col(uid: str, session_id: str) -> firestore.CollectionReference:
    return _session_doc(uid, session_id).collection("messages")

def _summaries_col(uid: str, session_id: str) -> firestore.CollectionReference:
    return _session_doc(uid, session_id).collection("summaries")

def _assignments_col(uid: str) -> firestore.CollectionReference:
    return _user_doc(uid).collection("assignments")

def _practice_logs_col(uid: str) -> firestore.CollectionReference:
    return _user_doc(uid).collection("practice_logs")

def _events_col(uid: str) -> firestore.CollectionReference:
    return _user_doc(uid).collection("events")

def _spendings_col(uid: str) -> firestore.CollectionReference:
    # 신규 규격: spending_records, 레거시 호환: spendings
    return _user_doc(uid).collection("spending_records")

def _legacy_spendings_col(uid: str) -> firestore.CollectionReference:
    return _user_doc(uid).collection("spendings")

# ------------------------------------------------------------------------------
# F1) 주간 상담 세션 (세션 라이프사이클)
# ------------------------------------------------------------------------------
def start_session(uid: str, week: int, resume: bool = False) -> Dict[str, Any]:
    """
    F1.1, F1.4: 세션 생성/재개
    status: draft|active|paused|ended
    """
    _required(uid, "uid")
    if not (1 <= int(week) <= 10):
        raise ValueError("week must be 1..10")

    # 재개: 해당 주차 active/paused/draft 중 최신 세션 찾기
    if resume:
        q = (
            _sessions_col(uid)
            .where("week", "==", int(week))
            .where("status", "in", ["draft", "active", "paused"])
        )
        docs = _safe_order(q, "started_at", direction=firestore.Query.DESCENDING)
        for d in docs:
            data = d.to_dict()
            return {
                "session_id": d.id,
                "week": data.get("week"),
                "status": data.get("status"),
                "state": data.get("state", {}),
                "started_at": _to_iso(data.get("started_at")),
            }

    # 새로 시작
    ref = _sessions_col(uid).document()
    payload = {
        "user_id": uid,
        "week": int(week),
        "status": "active",
        "protocol_version": "1.0.0",
        "started_at": firestore.SERVER_TIMESTAMP,
        "state": {},
    }
    ref.set(payload)
    return {
        "session_id": ref.id,
        "week": int(week),
        "status": "active",
        "state": {},
    }

def append_message(uid: str, session_id: str, role: Literal["user", "assistant", "system"], text: str, step_key: Optional[str] = None) -> str:
    """
    메시지 기록 (F1 연동 / 메시지 히스토리)
    """
    _required(uid, "uid")
    _required(session_id, "session_id")
    _required(role, "role")
    _required(text, "text")

    mref = _messages_col(uid, session_id).document()
    mref.set({
        "session_id": session_id,
        "user_id": uid,
        "role": role,
        "text": text,
        "step_key": step_key,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return mref.id

def update_session_state(uid: str, session_id: str, state: Dict[str, Any], step_key: Optional[str] = None):
    """
    세션 state 업데이트 (상태머신 진행)
    """
    _required(uid, "uid")
    _required(session_id, "session_id")
    _session_doc(uid, session_id).set({
        "state": state,
        "step_key": step_key,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)

def end_session(uid: str, session_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    F1.3: 세션 종료
    """
    _required(uid, "uid")
    _required(session_id, "session_id")
    doc = _session_doc(uid, session_id)
    doc.set({
        "status": "ended",
        "ended_at": firestore.SERVER_TIMESTAMP,
        "end_reason": reason,
    }, merge=True)
    return {"session_id": session_id, "status": "ended"}

def get_active_session(uid: str) -> Dict[str, Any]:
    """
    현재 활성 세션 조회 (F1 보조)
    """
    _required(uid, "uid")
    q = _sessions_col(uid).where("status", "in", ["active", "draft", "paused"])
    docs = _safe_order(q, "started_at", direction=firestore.Query.DESCENDING)
    for d in docs:
        data = d.to_dict()
        return {
            "session_id": d.id,
            "week": data.get("week"),
            "status": data.get("status"),
        }
    return {"session_id": None, "week": None, "status": None}

# ------------------------------------------------------------------------------
# F1.3: 세션 요약 + 숙제 저장/조회
# ------------------------------------------------------------------------------
def save_summary(uid: str, session_id: str, summary_data: Dict[str, Any]) -> Dict[str, str]:
    """
    기존 코드 호환: users/{uid}/sessions/{session_id}/summaries/{autoId}
    summary_data: { emotion, spending, action, ... }
    """
    _required(uid, "uid")
    _required(session_id, "session_id")
    ref = _summaries_col(uid, session_id).document()
    payload = {
        "uid": uid,
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        **(summary_data or {}),
    }
    ref.set(payload)
    return {"counseling_id": ref.id}

def get_summaries_by_session(uid: str, session_id: str) -> List[Dict[str, Any]]:
    _required(uid, "uid")
    _required(session_id, "session_id")
    col = _summaries_col(uid, session_id)
    try:
        docs = col.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    except FailedPrecondition:
        docs = col.stream()
    out: List[Dict[str, Any]] = []
    for d in docs:
        item = d.to_dict()
        item["timestamp"] = _to_iso(item.get("timestamp"))
        item["counseling_id"] = d.id
        out.append(item)
    # 안전 정렬
    out.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return out

def get_counseling_detail(uid: str, session_id: str, counseling_id: str) -> Optional[Dict[str, Any]]:
    _required(uid, "uid")
    _required(session_id, "session_id")
    _required(counseling_id, "counseling_id")
    ref = _summaries_col(uid, session_id).document(counseling_id)
    snap = ref.get()
    if not snap.exists:
        return None
    data = snap.to_dict()
    data["timestamp"] = _to_iso(data.get("timestamp"))
    data["counseling_id"] = counseling_id
    return data

# ------------------------------------------------------------------------------
# F2) 일일 실습 체크인 (Practice Logs)
# ------------------------------------------------------------------------------
def upsert_assignment(uid: str, session_id: str, assignment: Dict[str, Any]) -> Dict[str, Any]:
    """
    F1.3: 숙제(Assignment) 저장 (세션 종료 시 생성)
    구조 예:
    { week, title, instructions, due_date, rubric: { target_days:int, min_daily_action: str } }
    """
    _required(uid, "uid")
    _required(session_id, "session_id")

    aref = _assignments_col(uid).document()
    body = {
        "assignment_id": aref.id,
        "session_id": session_id,
        "user_id": uid,
        "created_at": firestore.SERVER_TIMESTAMP,
        **assignment,
    }
    aref.set(body)
    return {"assignment_id": aref.id}

def get_current_assignment(uid: str, week: Optional[int] = None) -> Optional[Dict[str, Any]]:
    _required(uid, "uid")
    col = _assignments_col(uid)
    q = col
    if week is not None:
        q = col.where("week", "==", int(week))
    docs = _safe_order(q, "created_at", direction=firestore.Query.DESCENDING)
    for d in docs:
        item = d.to_dict()
        item["created_at"] = _to_iso(item.get("created_at"))
        return item
    return None

def create_practice_log(uid: str, payload: Dict[str, Any]) -> Dict[str, str]:
    """
    F2.1~2.3: 실습 로그 작성
    payload keys:
      - date(YYYY-MM-DD), assignment_id, adherence(0..100), obstacles[], mood(1..5), urge(0..10), notes
    """
    _required(uid, "uid")
    _required(payload.get("date"), "date")
    _required(payload.get("assignment_id"), "assignment_id")

    pref = _practice_logs_col(uid).document()
    body = {
        "user_id": uid,
        "created_at": firestore.SERVER_TIMESTAMP,
        **payload,
    }
    pref.set(body)
    return {"log_id": pref.id}

def query_practice_logs(uid: str, date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    """
    F2.3: 실습 로그 조회 + 통계 (adherence_avg, days_done)
    """
    _required(uid, "uid")
    col = _practice_logs_col(uid)
    q = col
    if date_from:
        q = q.where("date", ">=", date_from)
    if date_to:
        q = q.where("date", "<=", date_to)

    items: List[Dict[str, Any]] = []
    for s in _safe_order(q, "created_at", direction=firestore.Query.DESCENDING):
        d = s.to_dict()
        d["log_id"] = s.id
        d["created_at"] = _to_iso(d.get("created_at"))
        items.append(d)

    # 통계
    adherences = [x.get("adherence") for x in items if isinstance(x.get("adherence"), (int, float))]
    adherence_avg = round(sum(adherences) / len(adherences), 2) if adherences else 0.0
    days_done = len({x.get("date") for x in items if (x.get("adherence") or 0) > 0})

    return {"items": items, "stats": {"adherence_avg": adherence_avg, "days_done": days_done}}

# ------------------------------------------------------------------------------
# F3) 트리거/이벤트 (충동/근접)
# ------------------------------------------------------------------------------
def create_event(uid: str, payload: Dict[str, Any]) -> Dict[str, str]:
    """
    F3.1~3.3: 이벤트 생성
    payload 예:
      { occurred_at, amount, currency, place?, trigger?, emotion?, thought?, action, alt_action?, notes? }
    """
    _required(uid, "uid")
    _required(payload.get("occurred_at"), "occurred_at")
    _required(payload.get("action"), "action")

    eref = _events_col(uid).document()
    body = {
        "user_id": uid,
        "created_at": firestore.SERVER_TIMESTAMP,
        **payload,
    }
    eref.set(body)
    return {"event_id": eref.id}

def query_events(uid: str, from_iso: Optional[str], to_iso: Optional[str]) -> Dict[str, Any]:
    _required(uid, "uid")
    col = _events_col(uid)
    q = col
    if from_iso:
        q = q.where("occurred_at", ">=", from_iso)
    if to_iso:
        q = q.where("occurred_at", "<=", to_iso)

    items: List[Dict[str, Any]] = []
    for s in _safe_order(q, "occurred_at", direction=firestore.Query.DESCENDING):
        d = s.to_dict()
        d["event_id"] = s.id
        d["created_at"] = _to_iso(d.get("created_at"))
        items.append(d)
    return {"items": items}

# ------------------------------------------------------------------------------
# F4) 리포트 (일간/주간)
# ------------------------------------------------------------------------------
def get_daily_dashboard(uid: str, ymd: str) -> Dict[str, Any]:
    """
    F4.1: 일간 리포트
    - urges: 해당 날짜의 평균 충동(urge) (practice_logs 기반)
    - events: 해당 날짜 기록된 이벤트 수
    - adherence: 해당 날짜 실습 수행 평균
    - mood_avg: 해당 날짜 기분 평균
    - insights: 간단 규칙 기반 인사이트
    """
    _required(uid, "uid")
    # practice_logs
    pl_q = _practice_logs_col(uid).where("date", "==", ymd)
    practice_items: List[Dict[str, Any]] = []
    for s in _safe_order(pl_q, "created_at", direction=firestore.Query.ASCENDING):
        d = s.to_dict()
        practice_items.append(d)

    # events (발생 시각의 YYYY-MM-DD로 필터하기 위해 클라이언트가 ISO를 넣는 걸 전제)
    ev_q = _events_col(uid).where("occurred_at", ">=", f"{ymd}T00:00:00Z").where("occurred_at", "<=", f"{ymd}T23:59:59Z")
    event_items: List[Dict[str, Any]] = [s.to_dict() for s in _safe_order(ev_q, "occurred_at", direction=firestore.Query.ASCENDING)]

    urges_vals = [x.get("urge") for x in practice_items if isinstance(x.get("urge"), (int, float))]
    moods_vals = [x.get("mood") for x in practice_items if isinstance(x.get("mood"), (int, float))]
    adher_vals = [x.get("adherence") for x in practice_items if isinstance(x.get("adherence"), (int, float))]

    urges = round(sum(urges_vals) / len(urges_vals), 2) if urges_vals else 0
    mood_avg = round(sum(moods_vals) / len(moods_vals), 2) if moods_vals else 0
    adherence = round(sum(adher_vals) / len(adher_vals), 2) if adher_vals else 0

    insights: List[str] = []
    if adherence >= 60 and urges <= 4:
        insights.append("오늘은 실습 수행이 안정적이고 충동이 낮아요. 같은 시간대 루틴을 유지해보세요.")
    if any(x.get("trigger") == "SNS" or "인스타" in (x.get("trigger", "")) for x in event_items):
        insights.append("SNS 노출이 트리거라면, 앱 제한 타이머를 15분으로 설정해보세요.")
    if mood_avg <= 2 and adherence < 40:
        insights.append("컨디션 저하가 수행률에 영향을 주고 있어요. 쉬운 대체 행동을 1가지로 더 줄여보세요.")

    return {
        "date": ymd,
        "urges": urges,
        "events": len(event_items),
        "adherence": adherence,
        "mood_avg": mood_avg,
        "insights": insights,
    }

def get_weekly_dashboard(uid: str, week_idx: int) -> Dict[str, Any]:
    """
    F4.2: 주간 리포트(간단 버전)
    - adherence_trend: 해당 주차 실습 로그 일자 순 평균 수행률
    - urges_trend: 해당 주차 실습 로그 일자 순 평균 충동
    - wins: 텍스트 인사이트
    - focus: 다음 주 초점
    """
    _required(uid, "uid")
    if not (1 <= int(week_idx) <= 10):
        raise ValueError("week_idx must be 1..10")

    # 주차 매핑은 MVP에서 practice_logs.week 필드를 사용한다고 가정
    col = _practice_logs_col(uid).where("week", "==", int(week_idx))
    items = [s.to_dict() for s in _safe_order(col, "date", direction=firestore.Query.ASCENDING)]

    # 일자별 평균
    by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for it in items:
        if it.get("date"):
            by_date[it["date"]].append(it)

    adherence_trend: List[float] = []
    urges_trend: List[float] = []
    for dkey in sorted(by_date.keys()):
        day_items = by_date[dkey]
        ad = [x.get("adherence") for x in day_items if isinstance(x.get("adherence"), (int, float))]
        ug = [x.get("urge") for x in day_items if isinstance(x.get("urge"), (int, float))]
        adherence_trend.append(round(sum(ad) / len(ad), 2) if ad else 0.0)
        urges_trend.append(round(sum(ug) / len(ug), 2) if ug else 0.0)

    wins: List[str] = []
    if adherence_trend and max(adherence_trend) >= 70:
        wins.append("일부 날짜에서 수행률 70% 이상을 달성했어요.")
    if urges_trend and min(urges_trend) <= 3:
        wins.append("충동 강도가 낮은 날이 있었어요. 그 날 패턴을 복제해보세요.")

    focus = "다음 주는 '대체 행동 1가지'를 하루 동일 시간대에 반복해 루틴화하기"

    return {
        "week": int(week_idx),
        "adherence_trend": adherence_trend,
        "urges_trend": urges_trend,
        "wins": wins,
        "focus": focus,
    }

# ------------------------------------------------------------------------------
# F5) 알림 (서버 측에서는 스케줄 정보만 저장, 실제 전송은 별도 서비스/클라우드 스케줄러)
# ------------------------------------------------------------------------------
def save_push_schedule(uid: str, push_type: Literal["practice", "weekly_session"], local_time_hhmm: str) -> Dict[str, Any]:
    """
    F5.1~F5.2: 사용자의 푸시 스케줄 선호 저장
    - 실제 발송은 Cloud Scheduler/PubSub/FCM 조합으로 처리
    """
    _required(uid, "uid")
    if push_type not in ("practice", "weekly_session"):
        raise ValueError("type must be 'practice' or 'weekly_session'")
    if not isinstance(local_time_hhmm, str) or len(local_time_hhmm) != 5 or local_time_hhmm[2] != ":":
        raise ValueError("local_time must be 'HH:mm'")

    _user_doc(uid).set({
        "push_prefs": {
            push_type: {
                "local_time": local_time_hhmm,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        }
    }, merge=True)
    return {"scheduled": True}

# ------------------------------------------------------------------------------
# F6) 계정/인증 - (백엔드에선 Firebase Admin으로 토큰 검증, DB에는 최소 정보만)
# 별도 구현 필요 없음 (main.py에서 토큰 검증)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# F7) 관리자/디버그
# ------------------------------------------------------------------------------
def admin_force_session_status(uid: str, session_id: str, status: Literal["draft", "active", "paused", "ended"]) -> None:
    _required(uid, "uid")
    _required(session_id, "session_id")
    _session_doc(uid, session_id).set({
        "status": status,
        "admin_forced_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)

def admin_get_raw_state(uid: str, session_id: str) -> Dict[str, Any]:
    _required(uid, "uid")
    _required(session_id, "session_id")
    snap = _session_doc(uid, session_id).get()
    if not snap.exists:
        raise NotFound(f"session not found: {session_id}")
    data = snap.to_dict()
    data["started_at"] = _to_iso(data.get("started_at"))
    data["ended_at"] = _to_iso(data.get("ended_at"))
    return data

# ------------------------------------------------------------------------------
# 기존 main.py와의 호환 함수 (유누님 코드 그대로 동작)
# ------------------------------------------------------------------------------
def save_chat_log(uid: str, session_id: str, user_message: str, bot_response: dict):
    _required(uid, "uid")
    _required(session_id, "session_id")
    doc = {
        "uid": uid,
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "user_message": user_message,
        "bot_response": bot_response,
    }
    _messages_col(uid, session_id).add(doc)

def add_spending_record(uid: str, record: dict):
    """
    기존 spendings 컬렉션 호환 + 신규 spending_records로 저장
    """
    _required(uid, "uid")
    if not isinstance(record, dict):
        raise ValueError("record must be dict")

    # 신규 경로
    new_record = {
        **record,
        "uid": uid,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    _spendings_col(uid).add(new_record)

    # 레거시 경로도 유지 저장(원한다면 제거 가능)
    try:
        _legacy_spendings_col(uid).add(new_record)
    except Exception:
        pass

def get_spending_by_date(uid: str, yyyy_mm_dd: str, include_counseling_id: bool = False) -> List[Dict[str, Any]]:
    _required(uid, "uid")
    # 신규
    col_new = _spendings_col(uid)
    try:
        qn = col_new.where("date", "==", yyyy_mm_dd).order_by("created_at", direction=firestore.Query.ASCENDING)
        docs_new = qn.stream()
    except FailedPrecondition:
        docs_new = col_new.where("date", "==", yyyy_mm_dd).stream()

    items: List[Dict[str, Any]] = []
    for s in docs_new:
        d = s.to_dict()
        d["id"] = s.id
        d["created_at"] = _to_iso(d.get("created_at"))
        if not include_counseling_id:
            d.pop("counseling_id", None)
        items.append(d)

    # 레거시 병합(중복 id 회피를 위해 prefix)
    try:
        col_old = _legacy_spendings_col(uid)
        try:
            qo = col_old.where("date", "==", yyyy_mm_dd).order_by("created_at", direction=firestore.Query.ASCENDING)
            docs_old = qo.stream()
        except FailedPrecondition:
            docs_old = col_old.where("date", "==", yyyy_mm_dd).stream()
        for s in docs_old:
            d = s.to_dict()
            d["id"] = "legacy_" + s.id
            d["created_at"] = _to_iso(d.get("created_at"))
            if not include_counseling_id:
                d.pop("counseling_id", None)
            items.append(d)
    except Exception:
        pass

    items.sort(key=lambda x: x.get("created_at") or "")
    return items
