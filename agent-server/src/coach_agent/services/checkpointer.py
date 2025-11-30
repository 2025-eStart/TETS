# coach_agent/services/checkpointer.py

from __future__ import annotations

import asyncio
from typing import Optional, Iterator, AsyncIterator, Sequence, Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointTuple,
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
)

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter  # 필터 타입 명시

from coach_agent.services.firebase_admin_client import get_db


class FirestoreSaver(BaseCheckpointSaver):
    """
    LangGraph v0.2용 Firestore 기반 Checkpointer.
    
    저장 구조:
    - Collection: {collection}
    - Document: {thread_id}
    - SubCollection: checkpoints / {checkpoint_id}
    """

    def __init__(
        self,
        *,
        collection: str = "langgraph_checkpoints",
        serde=None,
    ) -> None:
        # v0.2에서는 serde를 따로 넘기지 않으면 알아서 기본값을 사용합니다.
        super().__init__(serde=serde)
        self.db = get_db()
        self.collection = collection

    # ---------- 내부 헬퍼 ----------

    def _get_checkpoint_col(self, thread_id: str):
        """checkpoints 서브 컬렉션 참조 반환"""
        return (
            self.db.collection(self.collection)
            .document(thread_id)
            .collection("checkpoints")
        )

    # ---------- Sync 구현 ----------

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        특정 thread_id의 체크포인트를 불러옵니다.
        """
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = config["configurable"].get("checkpoint_id") # v0.2 용어
        # 하위 호환성을 위해 thread_ts도 확인
        if not checkpoint_id:
            checkpoint_id = config["configurable"].get("thread_ts")

        if not thread_id:
            return None

        col = self._get_checkpoint_col(thread_id)

        # 1) checkpoint_id가 명시된 경우
        if checkpoint_id:
            doc_ref = col.document(checkpoint_id)
            snap = doc_ref.get()
            if not snap.exists:
                return None
            data = snap.to_dict()
        
        # 2) checkpoint_id가 없는 경우 (최신 상태 조회)
        else:
            # checkpoint_id는 사전순으로 정렬 가능하므로 내림차순 정렬하여 최신 1개 가져옴
            query = col.order_by("checkpoint_id", direction=firestore.Query.DESCENDING).limit(1)
            docs = list(query.stream())
            if not docs:
                return None
            data = docs[0].to_dict()

        # 데이터 역직렬화 (v0.2 필수 필드 포함)
        checkpoint = self.serde.loads(data["checkpoint"])
        metadata = self.serde.loads(data["metadata"])
        # parent_config는 저장 시점에 parent_checkpoint_id를 저장해두었다면 복원 가능 (여기선 생략)
        
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": data["checkpoint_id"],
                    "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=None,  # 필요시 구현
            pending_writes=[],   # v0.2 필수: DB에 writes를 따로 저장하지 않는다면 빈 리스트
        )

    def list(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        thread_id = config["configurable"].get("thread_id")
        if not thread_id:
            return

        col = self._get_checkpoint_col(thread_id)
        query = col.order_by("checkpoint_id", direction=firestore.Query.DESCENDING)

        # 'before' 필터링 (before ID보다 작은 ID들 검색)
        if before:
            before_id = before["configurable"].get("checkpoint_id") or before["configurable"].get("thread_ts")
            if before_id:
                query = query.where(filter=FieldFilter("checkpoint_id", "<", before_id))

        if limit:
            query = query.limit(limit)

        for doc in query.stream():
            data = doc.to_dict()
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": data["checkpoint_id"],
                    }
                },
                checkpoint=self.serde.loads(data["checkpoint"]),
                metadata=self.serde.loads(data["metadata"]),
                parent_config=None,
                pending_writes=[], 
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions, # v0.2 추가 인자
    ) -> RunnableConfig:
        """
        체크포인트를 저장합니다.
        중요: ID는 생성하는 것이 아니라 checkpoint['id']를 사용해야 합니다.
        """
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = checkpoint["id"] # 엔진이 생성한 ID 사용 (필수)

        if not thread_id:
             raise ValueError("FirestoreSaver.put: 'thread_id'가 config에 없습니다.")

        col = self._get_checkpoint_col(thread_id)
        
        # Firestore 저장 데이터 구성
        doc_data = {
            "checkpoint_id": checkpoint_id,
            "checkpoint": self.serde.dumps(checkpoint),
            "metadata": self.serde.dumps(metadata),
            "created_at": firestore.SERVER_TIMESTAMP, # 디버깅용 실제 시간
        }

        # 저장 실행
        col.document(checkpoint_id).set(doc_data)

        # 저장된 설정 반환
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """
        v0.2 필수 메서드: 보류 중인 쓰기 작업(Pending Writes) 저장.
        복잡한 트랜잭션 관리가 필요 없으면 pass로 두어도 되지만,
        메서드 자체는 존재해야 에러가 안 납니다.
        """
        pass 

    # ---------- Async 구현 (Non-blocking) ----------

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        # asyncio.to_thread를 사용하여 Blocking I/O를 별도 스레드로 격리
        return await asyncio.to_thread(self.get_tuple, config)

    async def alist(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        # list는 제너레이터이므로, 리스트로 가져와서 비동기로 처리
        loop = asyncio.get_running_loop()
        # iterator 생성을 스레드에서 실행
        iterator = await loop.run_in_executor(None, lambda: list(self.list(config, before=before, limit=limit)))
        for item in iterator:
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)
    
    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        return await asyncio.to_thread(self.put_writes, config, writes, task_id)


firestore_checkpointer = FirestoreSaver()