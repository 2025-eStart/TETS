# coach_agent/utils/_days_since.py
from datetime import datetime, timezone
from typing import Optional

# 날짜 계산 헬퍼 함수 
def _days_since(ts: Optional[datetime], now: datetime) -> int:
    """ 타임스탬프(ts)가 'now'로부터 며칠 전인지 계산합니다. """
    if not isinstance(ts, datetime):
        # 마지막 접속 기록이 없으면 (신규 유저) 0일로 처리
        return 0
    
    # Firestore 타임스탬프와 현재 시간의 timezone 통일
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
        
    delta = (now - ts)
    
    # 0.5일(12시간) 이상 차이나면 1일로 간주 (선택적)
    return delta.days if delta.days > 0 else 0