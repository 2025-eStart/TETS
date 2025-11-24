# coach_agent/config.py
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

class Settings(BaseModel):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")              # 1. 메인 대화용 모델
    OPENAI_TONE_MODEL: str = os.getenv("OPENAI_TONE_MODEL", "gpt-4o-mini")    # 2. 말투 교정용 후처리 모델 (단순 변환용, 가볍고 빠른 모델)
    
    SERVICE_AUTH_HEADER: str = os.getenv("SERVICE_AUTH_HEADER", "dev-secret")
    REPO_BACKEND: str = os.getenv("REPO_BACKEND", "firestore")  # .env에 REPO_BACKEND가 없으면 기본값 "firestore" 사용
    
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

settings = Settings()
