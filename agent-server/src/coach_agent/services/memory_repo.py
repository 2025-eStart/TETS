# coach_agent/services/memory_repo.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .base_repo import Repo

DB: Dict[str, Any] = {
    "users": {},           # user_id -> dict
    "weekly_sessions": {}, # (user_id, week) -> dict
    "messages": []         # list of {user_id, session_type, week, role, text, ts}
}

class MemoryRepo(Repo):
    def get_user(self, user_id: str) -> Dict[str, Any]:
        u = DB["users"].get(user_id)
        if not u:
            u = {"user_id": user_id, "current_week": 1, "program_status": "active", "last_seen_at": None}
            DB["users"][user_id] = u
        return u

    def upsert_user(self, user_id: str, patch: Dict[str, Any]) -> None:
        u = self.get_user(user_id); u.update(patch)

    def get_active_weekly_session(self, user_id: str, week: int) -> Optional[Dict[str, Any]]:
        return DB["weekly_sessions"].get((user_id, week))

    def create_weekly_session(self, user_id: str, week: int) -> Dict[str, Any]:
        s = {"user_id": user_id, "week": week, "status": "in_progress", "last_activity_at": datetime.now(timezone.utc),
             "checkpoint": {"step_index": 0}}
        DB["weekly_sessions"][(user_id, week)] = s
        return s

    def save_message(self, user_id: str, session_type: str, week: int, role: str, text: str) -> None:
        DB["messages"].append({
            "user_id": user_id, "session_type": session_type, "week": week,
            "role": role, "text": text, "ts": datetime.now(timezone.utc)
        })

    def update_progress(self, user_id: str, week: int, exit_hit: bool) -> None:
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        s["last_activity_at"] = datetime.now(timezone.utc)
        if exit_hit:
            s["status"] = "completed"
            u = self.get_user(user_id)
            if week < 10:
                u["current_week"] = week + 1
            else:
                u["program_status"] = "completed"

    def last_seen_touch(self, user_id: str) -> None:
        self.upsert_user(user_id, {"last_seen_at": datetime.now(timezone.utc)})

    def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        messages = [
            msg for msg in DB["messages"]
            if msg["user_id"] == user_id
            # 과거 세션 내용을 현재 상담 내용에 반영하기 위해 사용자의 모든 과거 메시지를 불러옴
        ]
        return sorted(messages, key=lambda m: m["ts"])
    
    # --- 요약 함수 2개 ---
    def save_session_summary(self, user_id: str, week: int, summary_text: str) -> None:
        s = self.get_active_weekly_session(user_id, week)
        if s:
            # weekly_sessions 딕셔너리에 'summary' 필드 추가
            s["summary"] = summary_text
            DB["weekly_sessions"][(user_id, week)] = s
        else:
            # (예외 처리) 요약할 세션이 없는 경우. 실제로는 create_weekly_session에서 생성됨.
            print(f"Warning: No active session to save summary for user {user_id}, week {week}")

    def get_past_summaries(self, user_id: str, current_week: int) -> List[Dict[str, Any]]:
        summaries = []
        # DB["weekly_sessions"]의 모든 키 (user_id, week) 를 순회
        for (uid, week) in DB["weekly_sessions"]:
            if uid == user_id and week < current_week:
                session = DB["weekly_sessions"][(uid, week)]
                if "summary" in session:
                    summaries.append({
                        "week": week,
                        "session_type": "weekly", # 요약본은 항상 'weekly'
                        "summary": session["summary"]
                    })
        # 주차 순서대로 정렬
        return sorted(summaries, key=lambda s: s["week"])