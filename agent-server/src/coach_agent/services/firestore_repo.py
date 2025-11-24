# coach_agent/services/firestore_repo.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from coach_agent.services.base_repo import Repo
from coach_agent.services.firebase_admin_client import get_db
from firebase_admin import firestore
from google.api_core.exceptions import FailedPrecondition, NotFound
from google.cloud.firestore_v1 import FieldFilter

db = get_db()

def _user_doc(uid: str):
    return db.collection("users").document(uid)

def _sessions_col(uid: str):
    return _user_doc(uid).collection("sessions")

def _weekly_key(user_id: str, week: int):
    # 메모리에서는 (user_id, week) 키를 썼지만, Firestore에선 세션 도큐먼트로 일치시킴
    return f"w{week}"

class FirestoreRepo(Repo):
    def get_user(self, user_id: str) -> Dict[str, Any]:
        ref = _user_doc(user_id)
        snap = ref.get()
        if not snap.exists:
            doc = {"user_id": user_id, "current_week": 1, "program_status": "active", "last_seen_at": None}
            ref.set(doc)
            return doc
        return snap.to_dict()

    def upsert_user(self, user_id: str, patch: Dict[str, Any]) -> None:
        _user_doc(user_id).set(patch, merge=True)

    def get_active_weekly_session(self, user_id: str, week: int) -> Optional[Dict[str, Any]]:
        q = (_sessions_col(user_id)
             .where(filter=FieldFilter("week", "==", int(week)))
             .where(filter=FieldFilter("status", "in", ["draft", "active", "paused"])))
        try:
            docs = q.order_by("started_at", direction=firestore.Query.DESCENDING).stream()
        except FailedPrecondition:
            docs = q.stream()
        for d in docs:
            it = d.to_dict(); it["id"] = d.id
            return it
        return None

    def create_weekly_session(self, user_id: str, week: int) -> Dict[str, Any]:
        ref = _sessions_col(user_id).document()
        body = {
            "user_id": user_id,
            "week": int(week),
            "status": "active",
            "started_at": firestore.SERVER_TIMESTAMP,
            "last_activity_at": firestore.SERVER_TIMESTAMP,
            "checkpoint": {"step_index": 0},
            "state": {},
        }
        ref.set(body)
        body["id"] = ref.id
        return body

    def save_message(self, user_id: str, session_type: str, week: int, role: str, text: str) -> None:
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        _sessions_col(user_id).document(s["id"]).collection("messages").add({
            "user_id": user_id, # Collection Group Query를 위해 user_id 추가
            "session_type": session_type,
            "week": week,
            "role": role,
            "text": text,
            "created_at": firestore.SERVER_TIMESTAMP,
        })

    def update_progress(self, user_id: str, week: int, exit_hit: bool) -> None:
        """
        진행도/최근 활동 시간만 갱신.
        주차 진급/프로그램 완료는 mark_session_as_completed / advance_to_next_week가 담당.
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        patch = {
            "last_activity_at": firestore.SERVER_TIMESTAMP
        }
        if exit_hit:
            # 여기서는 단순히 '이번 턴에서 exit_goal을 만족했다' 정도만 기록할 수도 있음
            patch["exit_hit_last_turn"] = True

        _sessions_col(user_id).document(s["id"]).set(patch, merge=True)

    # --- [1] 상담 완료 여부 기록 ---
    def mark_session_as_completed(self, user_id: str, week: int, completed_at: datetime) -> None:
        """
        현재 주차 세션을 completed로 표시하고,
        user 문서에 last_weekly_session_completed_at을 기록
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)

        # 1) 세션 문서 업데이트
        _sessions_col(user_id).document(s["id"]).set({
            "status": "ended",
            "completed_at": completed_at
        }, merge=True)

        # 2) 사용자 문서에 최근 완료 시점 기록
        _user_doc(user_id).set({
            "last_weekly_session_completed_at": completed_at
        }, merge=True)

    # --- [2] 상담 완료 후: 주차 진급 ---
    def advance_to_next_week(self, user_id: str) -> int:
        """
        user.current_week -> +1, 프로그램 완료 처리까지 담당.
        """
        u_ref = _user_doc(user_id)
        snap = u_ref.get()
        if snap.exists:
            u = snap.to_dict()
        else:
            u = {"user_id": user_id, "current_week": 1, "program_status": "active"}

        current_week = int(u.get("current_week", 1))
        next_week = current_week + 1

        if next_week <= 10:
            u_ref.set({"current_week": next_week}, merge=True)
            return next_week
        else:
            # 프로그램 완료 처리
            u_ref.set({"program_status": "completed"}, merge=True)
            return current_week

    # --- [3] 21일 <= 미접속기간 && 이번주 상담 미완료(마지막 상담 완료 날짜+7일 이후): week 1으로 롤백 ---
    def rollback_user_to_week_1(self, user_id: str) -> None:
        """
        21일 이상 미접속 시 프로그램을 week 1부터 다시 시작하게 롤백
        """
        _user_doc(user_id).set({
            "current_week": 1,
            "program_status": "active",
            "last_weekly_session_completed_at": None,
        }, merge=True)
        # 필요하면 sessions 컬렉션도 정리할 수 있음 (여기서는 그대로 둠)

    # --- [4] 24시간 <= 미접속 기간 < 21일 && 이번주 상담 미완료(마지막 상담 완료 날짜+7일 이후): 현재 주차 세션 재시작 ---
    def restart_current_week_session(self, user_id: str, week: int) -> None:
        """
        active/paused 세션을 다시 시작.
        CHECKPOINT/STATE도 초기화.
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        _sessions_col(user_id).document(s["id"]).set({
            "status": "active",
            "last_activity_at": firestore.SERVER_TIMESTAMP,
            "checkpoint": {"step_index": 0},    # 1. 진행 단계 초기화
            "state": {},                        # 2. 세션 상태 초기화
        }, merge=True)

    def last_seen_touch(self, user_id: str) -> None:
        self.upsert_user(user_id, {"last_seen_at": datetime.now(timezone.utc)})
        
    def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """
        user_id에 해당하는 모든 메시지를 Collection Group 쿼리로 가져옵니다.
        (참고: Firestore 콘솔에서 'messages' 컬렉션 그룹에 대한 
         (user_id, created_at) 색인 생성이 필요할 수 있습니다)
        """
        q = (db.collection_group("messages")
             .where(filter=FieldFilter("user_id", "==", user_id))
             .order_by("created_at"))
        
        try:
            docs = q.stream()
            return [d.to_dict() for d in docs]
        except FailedPrecondition as e:
            print(f"FIRESTORE ERROR: 'messages' 컬렉션 그룹에 대한 색인이 필요할 수 있습니다. {e}")
            return []
        except Exception as e:
            print(f"FIRESTORE ERROR: {e}")
            return []
        ''' 과거
        s = self.get_active_weekly_session(user_id, week)
        if not s:
            return []
        
        docs = (_sessions_col(user_id)
                .document(s["id"])
                .collection("messages")
                .order_by("created_at")
                .stream())
        
        return [d.to_dict() for d in docs]
        '''
        
    # --- 요약 함수 2개 ---
    def save_session_summary(self, user_id: str, week: int, summary_text: str) -> None:
        """현재 주차의 'active' 세션에 요약본을 병합(merge)"""
        s = self.get_active_weekly_session(user_id, week)
        if s and s.get("id"):
            try:
                _sessions_col(user_id).document(s["id"]).set({
                    "summary": summary_text,
                    "summary_created_at": firestore.SERVER_TIMESTAMP
                }, merge=True)
            except Exception as e:
                print(f"FIRESTORE ERROR: Failed to save summary for session {s['id']}: {e}")
        else:
            print(f"Warning: No active session found to save summary for user {user_id}, week {week}")

    def get_past_summaries(self, user_id: str, current_week: int) -> List[Dict[str, Any]]:
        """current_week '미만'의 모든 세션에서 'summary' 필드가 있는 문서를 가져옴"""
        q = (_sessions_col(user_id)
             .where(filter=FieldFilter("week", "<", int(current_week)))
             .where(filter=FieldFilter("summary", "!=", None)) # 'summary' 필드가 존재하는 문서만
             .order_by("week"))
        
        summaries = []
        try:
            docs = q.stream()
            for d in docs:
                data = d.to_dict()
                summaries.append({
                    "week": data.get("week"),
                    "session_type": "weekly", # 요약본은 항상 'weekly'
                    "summary": data.get("summary")
                })
            return summaries
        except Exception as e:
            print(f"FIRESTORE ERROR: Failed to get past summaries: {e}")
            return []
        
        
    # 과거 채팅 접근 서랍용
    def get_all_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        users/{uid}/sessions 컬렉션의 모든 문서를 최신순으로 가져옴
        """
        try:
            # created_at 기준 내림차순 (최신이 위로)
            docs = (_sessions_col(user_id)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .stream())
            
            results = []
            for d in docs:
                data = d.to_dict()
                data["id"] = d.id # 문서 ID 포함
                results.append(data)
            return results
            
        except Exception as e:
            print(f"FIRESTORE ERROR (get_all_sessions): {e}")
            return []