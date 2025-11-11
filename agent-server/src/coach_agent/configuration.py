# cbt_app/configuration.py
from dataclasses import dataclass
from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    """ Agent Server가 주입받을 설정값 정의 """
    user_id: str = "tester1" # 테스트용 기본값 설정. 실제 배포 시에는 반드시 주입 필요.

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig):
        """ RunnableConfig에서 값을 추출하는 표준 헬퍼 """
        # config 딕셔너리에서 "configurable" 키를 찾습니다.
        configurable = config.get("configurable", {})
        
        # user_id 값을 가져옵니다.
        user_id = configurable.get("user_id")
        # Studio에서 'user_id'를 안 보냈으면(None),
        # 에러를 내지 말고 [수정 1]의 기본값("tester1_default")을 사용합니다.
        if not user_id:
            # cls()는 dataclass가 기본값으로 객체를 생성하도록 합니다.
            return cls() 
            
        # Studio에서 'user_id'를 보냈으면, 그 값을 사용합니다.
        return cls(user_id=user_id)