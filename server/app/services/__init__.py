# app/services/__init__.py
import os
from server.app.services.base_repo import Repo
from server.app.services.memory_repo import MemoryRepo
REPO_BACKEND = os.getenv("REPO_BACKEND", "memory")

if REPO_BACKEND == "firestore":
    from app.services.firestore_repo import FirestoreRepo
    REPO: Repo = FirestoreRepo()
else:
    REPO: Repo = MemoryRepo()
