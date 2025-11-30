# coach_agent/rag/search.py

from __future__ import annotations

from functools import lru_cache
from typing import List
import os

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone


# ---- 내부 헬퍼: 임베딩 & 벡터스토어 초기화 ----

@lru_cache
def _get_embeddings() -> OpenAIEmbeddings:
    """
    CBT/CBD 코퍼스를 위해 사용하는 임베딩 모델.
    - 환경변수 EMBEDDING_MODEL 로 override 가능
    """
    model_name = os.getenv("EMBEDDING_MODEL")
    return OpenAIEmbeddings(model=model_name)


@lru_cache
def _get_vectorstore() -> PineconeVectorStore:
    """
    Pinecone 상의 CBT/CBD 전용 인덱스를 LangChain VectorStore로 래핑.
    """
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_CBT_INDEX_NAME")

    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not set.")
    if not index_name:
        raise RuntimeError("PINECONE_CBT_INDEX_NAME is not set.")

    # pinecone 클라이언트 초기화 (서버리스 기준)
    pc = Pinecone(api_key=api_key)

    # LangChain VectorStore 래퍼 생성
    embeddings = _get_embeddings()
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
        # namespace나 metadata 필터를 쓰고 있으면 여기서 추가 가능
        # namespace="cbt_corpus",
    )
    return vectorstore


# ---- 외부에서 사용할 RAG 검색 함수 ----

def search_cbt_corpus(query: str, top_k: int = 5) -> List[Document]:
    """
    CBT/CBD 전용 RAG 코퍼스에서 질의문(query)에 대한 관련 문서를 검색.
    
    Args:
        query: LLM이 던지는 자연어 질의 (예: "Socratic questioning for automatic thoughts")
        top_k: 상위 몇 개의 문서를 가져올지 (기본 5개)

    Returns:
        langchain_core.documents.Document 객체 리스트
        - 각 Document의 .page_content 에 텍스트
        - 각 Document의 .metadata 에 출처/테크닉/페이지 등 메타데이터
    """
    if not query or not query.strip():
        return []

    vectorstore = _get_vectorstore()

    # similarity_search → List[Document] 반환
    docs: List[Document] = vectorstore.similarity_search(
        query=query,
        k=top_k,
        # CBT/CBD 전용 필터가 있으면 여기 metadata_filter로 추가:
        # filter={"domain": "cbt_cbd"}
    )
    return docs
