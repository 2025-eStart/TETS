# coach_agent/services/base_repo.py
from typing import Optional, Dict, Any, List, Protocol
from datetime import datetime

class Repo(Protocol):
    def get_user(self, user_id: str) -> Dict[str, Any]: ...
    def upsert_user(self, user_id: str, patch: Dict[str, Any]) -> None: ...
    def get_active_weekly_session(self, user_id: str, week: int) -> Optional[Dict[str, Any]]: ...
    def create_weekly_session(self, user_id: str, week: int) -> Dict[str, Any]: ...
    def save_message(self, user_id: str, session_type: str, week: int, role: str, text: str) -> None: ...
    def update_progress(self, user_id: str, week: int, exit_hit: bool) -> None: ...
    def last_seen_touch(self, user_id: str) -> None: ...
    def get_messages(self, user_id: str) -> List[Dict[str, Any]]: ... # 주차 상관없이 user_id에 해당하는 '모든' 메시지를 반환
    # --- 요약 관련 함수 2개 ---
    def save_session_summary(self, user_id: str, week: int, summary_text: str) -> None: ...
    def get_past_summaries(self, user_id: str, current_week: int) -> List[Dict[str, Any]]: ...
    # --- 미접속 기간에 따른 세션 초기화/변경 로직 ---
    def mark_session_as_completed(self, user_id: str, week: int, completed_at: datetime) -> None:
        """
        현재 주차 세션을 '완료' 상태로 표시하고,
        user.last_weekly_session_completed_at 을 갱신한다.
        (current_week는 여기서 건드리지 않는다)
        """
        ...

    def advance_to_next_week(self, user_id: str) -> int:
        """
        user.current_week 을 +1 올리고, 새 current_week 값을 반환한다.
        10주차를 넘어가면 program_status='completed' 처리 등도 여기서 한다.
        """
        ...

    def rollback_user_to_week_1(self, user_id: str) -> None:
        """
        21일 이상 미접속 등 롤백 조건일 때
        current_week=1 등으로 초기화한다.
        (필요하다면 세션 상태도 함께 정리)
        """
        ...

    def restart_current_week_session(self, user_id: str, week: int) -> None:
        """
        미접속 후 동일 주차를 '다시 시작'할 때,
        세션 상태(status, checkpoint 등)를 초기화/재시작한다.
        """
        ...
        
    # 현재 주차 세션의 진행 단계(Step Index)를 저장
    def update_checkpoint(self, user_id: str, week: int, step_index: int) -> None: ...