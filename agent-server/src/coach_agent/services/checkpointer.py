# coach_agent/services/checkpointer.py

from __future__ import annotations

import asyncio
from typing import Optional, Iterator, AsyncIterator, Sequence, Any, List, Tuple

from langchain_core.runnables import RunnableConfig
from langchain_core.load import dumps as lc_dumps, loads as lc_loads
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointTuple,
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
)

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from coach_agent.services.firebase_admin_client import get_db

# -------------------------------------------------------------------------
# 1. 안전한 Serializer 정의
# -------------------------------------------------------------------------
class LangChainSerializer:
    def dumps(self, obj: Any) -> bytes:
        return lc_dumps(obj).encode("utf-8")

    def loads(self, data: bytes | str) -> Any:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return lc_loads(data)

# -------------------------------------------------------------------------
# 2. 표준 FirestoreSaver 구현 (SerializerCompat 충돌 해결판)
# -------------------------------------------------------------------------
class FirestoreSaver(BaseCheckpointSaver):
    """
    LangGraph BaseCheckpointSaver 명세를 준수하는 Firestore 구현체.
    """

    def __init__(
        self,
        *,
        collection: str = "langgraph_checkpoints",
        serde=None,
    ) -> None:
        # ✅ [핵심 수정] 부모 클래스가 self.serde를 래핑해버리므로, 
        # 원본 시리얼라이저를 self.serializer라는 별도 변수에 보관합니다.
        self.serializer = serde or LangChainSerializer()
        
        super().__init__(serde=self.serializer)
        
        self.db = get_db()
        self.collection = collection

    def _get_checkpoint_col(self, thread_id: str):
        return self.db.collection(self.collection).document(thread_id).collection("checkpoints")

    # ---------------------------------------------------------------------
    # (1) GET TUPLE
    # ---------------------------------------------------------------------
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        if not checkpoint_id:
            checkpoint_id = config["configurable"].get("thread_ts")

        if not thread_id:
            return None

        col = self._get_checkpoint_col(thread_id)

        if checkpoint_id:
            doc_ref = col.document(checkpoint_id)
            snap = doc_ref.get()
        else:
            query = col.order_by("checkpoint_id", direction=firestore.Query.DESCENDING).limit(1)
            docs = list(query.stream())
            snap = docs[0] if docs else None

        if not snap or not snap.exists:
            return None

        data = snap.to_dict()
        
        # Writes 조회
        writes_col = snap.reference.collection("writes")
        pending_writes: List[Tuple[str, Any, str]] = []
        
        for w_doc in writes_col.stream():
            w_data = w_doc.to_dict()
            pending_writes.append((
                w_data["task_id"],
                w_data["channel"],
                # ✅ self.serde 대신 self.serializer 사용
                self.serializer.loads(w_data["value"])
            ))

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": data["checkpoint_id"],
                    "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                }
            },
            # ✅ self.serde 대신 self.serializer 사용
            checkpoint=self.serializer.loads(data["checkpoint"]),
            metadata=self.serializer.loads(data["metadata"]),
            parent_config=data.get("parent_config"),
            pending_writes=pending_writes,
        )

    # ---------------------------------------------------------------------
    # (2) LIST
    # ---------------------------------------------------------------------
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
                # ✅ self.serde 대신 self.serializer 사용
                checkpoint=self.serializer.loads(data["checkpoint"]),
                metadata=self.serializer.loads(data["metadata"]),
                parent_config=data.get("parent_config"),
                pending_writes=[], 
            )

    # ---------------------------------------------------------------------
    # (3) PUT
    # ---------------------------------------------------------------------
    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = checkpoint["id"]

        if not thread_id:
             raise ValueError("FirestoreSaver.put: 'thread_id'가 config에 없습니다.")

        col = self._get_checkpoint_col(thread_id)
        
        # ✅ self.serde 대신 self.serializer 사용 (여기서 에러 해결!)
        cp_bytes = self.serializer.dumps(checkpoint)
        mt_bytes = self.serializer.dumps(metadata)

        doc_data = {
            "checkpoint_id": checkpoint_id,
            "checkpoint": cp_bytes.decode("utf-8"),
            "metadata": mt_bytes.decode("utf-8"),
            "parent_config": config.get("configurable", {}).get("thread_ts"),
            "created_at": firestore.SERVER_TIMESTAMP,
        }

        col.document(checkpoint_id).set(doc_data)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    # ---------------------------------------------------------------------
    # (4) PUT WRITES
    # ---------------------------------------------------------------------
    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]], 
        task_id: str, 
    ) -> None:
        thread_id = config["configurable"].get("thread_id")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if not thread_id or not checkpoint_id:
            return

        writes_col = self._get_checkpoint_col(thread_id).document(checkpoint_id).collection("writes")
        batch = self.db.batch()
        
        for idx, (channel, value) in enumerate(writes):
            write_doc_ref = writes_col.document(f"{task_id}_{idx:03d}")
            
            # ✅ self.serde 대신 self.serializer 사용
            val_bytes = self.serializer.dumps(value)
            
            batch.set(write_doc_ref, {
                "task_id": task_id,
                "channel": channel,
                "value": val_bytes.decode("utf-8"),
                "idx": idx
            })
            
        batch.commit()

    # ---------------------------------------------------------------------
    # (5) Async Wrappers
    # ---------------------------------------------------------------------
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return await asyncio.to_thread(self.get_tuple, config)

    async def alist(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        loop = asyncio.get_running_loop()
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

# 인스턴스 생성
firestore_checkpointer = FirestoreSaver()