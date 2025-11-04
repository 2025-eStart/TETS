from typing import Literal, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

SessionType = Literal["WEEKLY", "DAILY", "GENERAL"]

class State(BaseModel):
    user_id: str
    now_utc: datetime
    session_type: SessionType = "WEEKLY"

    user: Dict[str, Any] = {}
    weekly_session: Optional[Dict[str, Any]] = None
    daily_session: Optional[Dict[str, Any]] = None
    current_week: int = 1
    protocol: Dict[str, Any] = {}

    metrics: Dict[str, Any] = {}
    intervention_level: Optional[str] = None  # "L1".."L5"
    prompt: Dict[str, Any] = {}
    llm_output: Optional[str] = None

    exit: bool = False
    expired: bool = False
