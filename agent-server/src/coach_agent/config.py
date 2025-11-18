# coach_agent/config.py
from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseModel):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    SERVICE_AUTH_HEADER: str = os.getenv("SERVICE_AUTH_HEADER", "dev-secret")
    REPO_BACKEND: str = os.getenv("REPO_BACKEND", "memory")  # "firestore" 로 교체 가능
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

settings = Settings()
