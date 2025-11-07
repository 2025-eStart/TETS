from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.services.base_repo import Repo

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

# [추가] get_messages 구현
    def get_messages(self, user_id: str, week: int) -> List[Dict[str, Any]]:
        messages = [
            msg for msg in DB["messages"]
            if msg["user_id"] == user_id 
               and msg["week"] == week 
               and msg["session_type"] == "weekly"
        ]
        return sorted(messages, key=lambda m: m["ts"])
    
# REPO: Repo = MemoryRepo() => 삭제: __init__.py에서 관리