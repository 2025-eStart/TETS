# coach_agent/rag/search.py

from __future__ import annotations

from functools import lru_cache
from typing import List
import os
import time

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

# RAG 필요성 판단을 위해 RAG 검색 on/off 위한 플래그
RAG_ENABLED = os.getenv("ENABLE_RAG", "false").lower() == "true"

# ---- 내부 헬퍼: 임베딩 & 벡터스토어 초기화 ----

@lru_cache
def _get_embeddings() -> HuggingFaceEmbeddings:
    model_name = os.getenv("EMBEDDING_MODEL")
    
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


@lru_cache
def _get_vectorstore() -> PineconeVectorStore:
    """
    Pinecone v3 + LangChain-Pinecone 공식 연동
    """
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_CBT_INDEX_NAME")

    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not set.")
    if not index_name:
        raise RuntimeError("PINECONE_CBT_INDEX_NAME is not set.")

    # 1. Pinecone Client (v3) 인스턴스 생성
    pc = Pinecone(api_key=api_key)
    
    # 2. Index 객체 가져오기
    pinecone_index = pc.Index(index_name)

    # 3. Embeddings 준비
    embeddings = _get_embeddings()
    
    # 4. LangChain VectorStore 생성 (신형 방식)
    # 신형 패키지는 index 객체를 직접 받습니다.
    vectorstore = PineconeVectorStore(
        index=pinecone_index,
        embedding=embeddings,
        text_key="text"  # Pinecone 메타데이터 필드명 (보통 'text' 또는 'page_content')
    )
    
    return vectorstore


# ---- 외부에서 사용할 RAG 검색 함수 ----

def search_cbt_corpus(query: str, top_k: int = 5) -> List[Document]:
    """
    CBT/CBD 전용 RAG 코퍼스 검색
    """
    if not query or not query.strip():
        return []

    try:
        vectorstore = _get_vectorstore()
        
        # 검색 실행
        docs: List[Document] = vectorstore.similarity_search(
            query=query,
            k=top_k
        )
        return docs
    except Exception as e:
        print(f"[RAG Search Error] {e}")
        # 에러가 나도 챗봇이 죽지 않도록 빈 리스트 반환
        return []