# coach_agent/services/__init__.py
import os
from coach_agent.services.base_repo import Repo
from coach_agent.services.memory_repo import MemoryRepo
from coach_agent.settings import settings

# 1. 환경 변수 읽기
REPO_BACKEND = settings.REPO_BACKEND
print(f"👀 [Services] 초기화 모드: {REPO_BACKEND}") #디버깅

# 2. Firebase 모드면 저장소 객체 생성
if REPO_BACKEND == "firestore":
    from coach_agent.services.firestore_repo import FirestoreRepo
    print("🔥 FirestoreRepo 생성 시도 중...")
    REPO: Repo = FirestoreRepo()
    print(f"✅ FirestoreRepo 객체 생성 성공: {REPO}")
else:
    REPO: Repo = MemoryRepo()
    print(f"🧠 MemoryRepo(임시 저장소)가 선택되었습니다.")
