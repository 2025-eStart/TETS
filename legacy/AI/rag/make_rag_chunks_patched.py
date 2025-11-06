# make_rag_chunks.py
import os, json, hashlib, uuid, re
from pathlib import Path
from typing import List, Dict, Any

# 최신 import (langchain-community)
from langchain_community.document_loaders import (
    DirectoryLoader, PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, NotebookLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

# (선택) 토큰 길이 측정
try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
except Exception:
    enc = None

# ====== 설정 ======
INPUT_DIR = "./papers"            # 입력 폴더
OUTPUT_JSONL = "./chunks.jsonl"   # JSONL 결과
OUTPUT_TXT_DIR = "./chunks_txt"   # 청크 TXT 저장 폴더
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EXTS = ("pdf",)                   # 필요 시 ("pdf","txt","md","ipynb")
DOC_ID_PREFIX = "paper"
MIN_CHUNK_CHARS = 100             # 너무 짧은 청크 제거 기준
# ===================

LOADER_DICT = {
    "pdf": PyPDFLoader,
    "txt": TextLoader,
    "md": UnstructuredMarkdownLoader,
    "ipynb": NotebookLoader,
}



def decode_slashC_encoding(s: str) -> str:
    import re
    return re.sub(r"/C(\d{1,3})", lambda m: chr(int(m.group(1))), s)
def clean_text(text: str) -> str:
    # 1) Fix '/C###' decimal-escaped chars
    text = decode_slashC_encoding(text)
    # 2) Basic whitespace normalization
    return " ".join(text.split())

def load_documents(folder: str, exts=EXTS):
    docs = []
    for ext in exts:
        loader_cls = LOADER_DICT[ext]
        loader = DirectoryLoader(folder, glob=f"*.{ext}", loader_cls=loader_cls, show_progress=True)
        loaded = loader.load()
        for d in loaded:
            d.page_content = clean_text(d.page_content)
            src = d.metadata.get("source", "")
            d.metadata["filename"] = Path(src).name if src else "unknown"
        docs.extend(loaded)
    return docs

def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)

def md5_of_text(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def token_len(text: str) -> int:
    return len(enc.encode(text)) if enc else 0

def build_items(split_docs) -> List[Dict[str, Any]]:
    out = []
    name2id = {}
    for i, d in enumerate(split_docs):
        filename = d.metadata.get("filename", "unknown")
        page = d.metadata.get("page", None)
        if filename not in name2id:
            name2id[filename] = f"{DOC_ID_PREFIX}-{uuid.uuid4().hex[:8]}"
        doc_id = name2id[filename]

        content = (d.page_content or "").strip()
        if not content or len(content) < MIN_CHUNK_CHARS:
            continue

        h = md5_of_text(f"{filename}|{page}|{content[:600]}")
        out.append({
            "doc_id": doc_id,
            "filename": filename,
            "page": page,
            "chunk_id": i,
            "content": content,
            "num_tokens": token_len(content),
            "source": d.metadata.get("source", filename),
            "hash": h,
        })
    return out

def dedupe_by_hash(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen, uniq = set(), []
    for it in items:
        if it["hash"] in seen:
            continue
        seen.add(it["hash"])
        uniq.append(it)
    return uniq

def save_jsonl(items: List[Dict[str, Any]], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def safe_slug(name: str, maxlen: int = 40) -> str:
    # 파일명 안전 문자열 (영문/숫자/_/-만) + 길이 제한
    base = re.sub(r"[^A-Za-z0-9_\-]+", "_", name)
    return base[:maxlen].strip("_") or "chunk"

def save_chunks_as_txt(items: List[Dict[str, Any]], outdir: str):
    odir = Path(outdir)
    odir.mkdir(parents=True, exist_ok=True)
    counters = {}
    for it in items:
        # 파일명: <docslug>_p<page>_c<chunkid>.txt (중복 방지 카운터 포함)
        docslug = safe_slug(Path(it["filename"]).stem)
        page = it.get("page")
        page_part = f"p{page}" if page is not None else "pNA"
        base = f"{docslug}_{page_part}_c{it['chunk_id']}"
        # 혹시 동일 이름 충돌 시 뒤에 -n
        counters.setdefault(base, 0)
        counters[base] += 1
        suffix = f"-{counters[base]}" if counters[base] > 1 else ""
        fname = f"{base}{suffix}.txt"

        # (선택) 메타데이터 헤더를 파일 상단에 포함하고 싶다면 아래 주석 해제
        # header = (
        #     f"# doc_id: {it['doc_id']}\n"
        #     f"# filename: {it['filename']}\n"
        #     f"# page: {it['page']}\n"
        #     f"# chunk_id: {it['chunk_id']}\n"
        #     f"# tokens: {it['num_tokens']}\n"
        #     f"# source: {it['source']}\n"
        #     f"# hash: {it['hash']}\n\n"
        # )
        # text = header + it["content"]

        text = it["content"]  # 헤더 없이 본문만 저장
        (odir / fname).write_text(text, encoding="utf-8")

def main():
    if not Path(INPUT_DIR).exists():
        raise FileNotFoundError(f"입력 폴더가 없습니다: {INPUT_DIR}")

    print(f"[1/4] 문서 로딩 중...")
    docs = load_documents(INPUT_DIR, EXTS)
    print(f"  - 로딩된 문서 수: {len(docs)}")

    print(f"[2/4] 청크 분할 중 (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    split_docs = split_documents(docs)
    print(f"  - 분할 후 청크 수: {len(split_docs)}")

    print(f"[3/4] 메타데이터/해시 부착 & 중복 제거...")
    items = dedupe_by_hash(build_items(split_docs))
    print(f"  - 유니크 청크 수: {len(items)}")
    if not items:
        print("  - 저장할 청크가 없습니다(너무 짧거나 빈 청크). 설정값을 조정해 보세요.")
        return

    print(f"[4/4] 저장: JSONL -> {OUTPUT_JSONL}, TXT -> {OUTPUT_TXT_DIR}/")
    save_jsonl(items, OUTPUT_JSONL)
    save_chunks_as_txt(items, OUTPUT_TXT_DIR)
    print("완료! 🎉")

if __name__ == "__main__":
    main()
