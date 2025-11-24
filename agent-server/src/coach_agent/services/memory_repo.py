# coach_agent/services/memory_repo.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from coach_agent.services.base_repo import Repo

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
        """
        진행도(최근 활동 시간 등)만 갱신한다.
        주차 진급/완료 판단은 mark_session_as_completed / advance_to_next_week가 담당.
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        s["last_activity_at"] = datetime.now(timezone.utc)
        DB["weekly_sessions"][(user_id, week)] = s

    # --- 미접속 기간에 따른 세션 초기화/유지 메서드들 ---

    def mark_session_as_completed(self, user_id: str, week: int, completed_at: datetime) -> None:
        """
        현재 주차 세션 완료 + 사용자 last_weekly_session_completed_at 업데이트
        (current_week는 여기서 바꾸지 않는다)
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        s["status"] = "completed"
        s["completed_at"] = completed_at
        DB["weekly_sessions"][(user_id, week)] = s

        u = self.get_user(user_id)
        u["last_weekly_session_completed_at"] = completed_at

    def advance_to_next_week(self, user_id: str) -> int:
        """
        current_week +1 또는 프로그램 완료 처리 후 새 current_week 반환
        """
        u = self.get_user(user_id)
        current_week = u.get("current_week", 1)
        next_week = current_week + 1

        if next_week <= 10:
            u["current_week"] = next_week
        else:
            u["program_status"] = "completed"
            # 프로그램 완료 후 current_week를 굳이 늘릴 필요 없다면 유지
            next_week = current_week

        return u.get("current_week", next_week)

    def rollback_user_to_week_1(self, user_id: str) -> None:
        """
        21일 이상 미접속 시 week 1로 롤백
        """
        u = self.get_user(user_id)
        u["current_week"] = 1
        u["program_status"] = "active"
        u["last_weekly_session_completed_at"] = None
        # 필요하면 weekly_sessions도 정리 가능 (여기선 남겨둠)

    def restart_current_week_session(self, user_id: str, week: int) -> None:
        """
        현재 주차 세션 재시작: 상태 초기화 정도만 수행
        """
        s = self.get_active_weekly_session(user_id, week) or self.create_weekly_session(user_id, week)
        s["status"] = "in_progress"
        s["last_activity_at"] = datetime.now(timezone.utc)
        # 체크포인트/상태를 초기화하고 싶다면 여기서 처리
        s["checkpoint"] = {"step_index": 0}
        DB["weekly_sessions"][(user_id, week)] = s        

    def last_seen_touch(self, user_id: str) -> None:
        self.upsert_user(user_id, {"last_seen_at": datetime.now(timezone.utc)})

 # --- 서랍 기능: 모든 세션 조회 함수 ---
    def get_all_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        유저의 모든 세션(주간 상담 등)을 리스트로 반환.
        MemoryRepo 구조상 (user_id, week) 키를 순회하여 찾음.
        """
        results = []

        # 1. 모든 주간 세션 순회
        for (uid, week), session_data in DB["weekly_sessions"].items():
            if uid == user_id:
                # 데이터 원본 훼손 방지를 위해 복사
                s = session_data.copy()

                # 2. main.py 호환성을 위한 필드 보정
                # (MemoryRepo는 저장 시 id, created_at 등을 안 넣었을 수 있음)
                
                # ID가 없으면 임의로 생성 (UI에서 구분용)
                if "id" not in s:
                    s["id"] = f"weekly_{uid}_{week}"
                
                # session_type이 없으면 WEEKLY로 가정
                if "session_type" not in s:
                    s["session_type"] = "WEEKLY"
                
                # created_at이 없으면 last_activity_at을 사용 (정렬용)
                if "created_at" not in s:
                    s["created_at"] = s.get("last_activity_at", datetime.now(timezone.utc))

                results.append(s)

        # 3. 최신순 정렬 (created_at 기준 내림차순)
        # datetime 객체끼리 비교하여 정렬
        results.sort(key=lambda x: x["created_at"], reverse=True)

        return results
 
    def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        messages = [
            msg for msg in DB["messages"]
            if msg["user_id"] == user_id
            # 과거 세션 내용을 현재 상담 내용에 반영하기 위해 사용자의 모든 과거 메시지를 불러옴
        ]
        return sorted(messages, key=lambda m: m["ts"])
    
    # --- 요약 함수 ---
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
    