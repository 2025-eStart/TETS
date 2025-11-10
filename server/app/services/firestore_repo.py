# app/services/firestore_repo.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.services.base_repo import Repo
from app.services.firebase_admin_client import get_db
from firebase_admin import firestore
from google.api_core.exceptions import FailedPrecondition

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
             .where("week", "==", int(week))
             .where("status", "in", ["draft", "active", "paused"]))
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
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        patch = {"last_activity_at": firestore.SERVER_TIMESTAMP}
        if exit_hit:
            patch["status"] = "ended"
            # 주차 진도 올리기
            u = self.get_user(user_id)
            next_week = week + 1
            if next_week <= 10:
                self.upsert_user(user_id, {"current_week": next_week})
            else:
                self.upsert_user(user_id, {"program_status": "completed"})
        _sessions_col(user_id).document(s["id"]).set(patch, merge=True)

    def last_seen_touch(self, user_id: str) -> None:
        self.upsert_user(user_id, {"last_seen_at": datetime.now(timezone.utc)})
        
        
        # [추가] get_messages 구현
    def get_messages(self, user_id: str, week: int) -> List[Dict[str, Any]]:
        """
        user_id에 해당하는 모든 메시지를 Collection Group 쿼리로 가져옵니다.
        (참고: Firestore 콘솔에서 'messages' 컬렉션 그룹에 대한 
         (user_id, created_at) 색인 생성이 필요할 수 있습니다)
        """
        q = (db.collection_group("messages")
             .where("user_id", "==", user_id)
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