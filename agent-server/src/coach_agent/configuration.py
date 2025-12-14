# coach_agent/Context.py
""" Agent Server가 주입받을 설정값 정의 """

from dataclasses import dataclass
from typing import Optional, Literal
from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    # 1. user_id는 이제 필수로 취급 (기본값 제거 또는 None 처리)
    user_id: str = "tester"  # 기본값을 "tester"로 설정하여 langsmith 디버깅 시 에러 방지
    
    # 2. API 서버가 내린 결정을 주입받을 필드 추가
    session_type_override: Optional[Literal["WEEKLY", "GENERAL"]] = None 

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig):
        """ RunnableConfig에서 값을 추출 """
        configurable = config.get("configurable", {})
        
        # main.py에서 넘겨준 값들을 여기서 꺼냅니다.
        user_id = configurable.get("user_id")
        session_type = configurable.get("session_type_override")
        
        # user_id가 없으면 에러를 내거나, 안전하게 처리 (여기서는 에러 방지용 임시값)
        if not user_id:
            # 실제 배포시에는 raise ValueError("user_id is required")로 수정
            user_id = "anonymous_user" 
            
        return cls(
            user_id=user_id,
            session_type_override=session_type
        )