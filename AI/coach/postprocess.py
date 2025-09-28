"""
postprocess.py  —  최종 응답을 '예쁘고 일관되게' 다듬는 모듈
================================================================

이 모듈은 **LLM이 생성한 응답**과 **정책 셀렉터가 고른 대체행동**을 합쳐,
우리 제품 규칙(채팅 1턴=대체행동 2~3개, 글자수/단락/이모지 제한, 꼬리멘트 이모지 보장 등)에
맞게 **후처리(post-processing)** 합니다.

핵심 흐름
---------
1) `prepare_alternatives()`  
   - LLM 후보와 정책 후보를 **머지**하고,  
   - 문체를 **~하기** 형태로 최대한 통일,  
   - **길이 제한(≤90자)**, **중복 제거(토큰 자카드 유사도)**, **금칙어 필터** 등을 적용하여  
   - 규칙에 맞는 **2~3개** 대체행동 리스트를 만듭니다.

2) `enforce_response()`  
   - summary/fox_tail에 대해 **단락(≤2)**, **이모지(≤2)**, **길이(요약 ≤300자)** 제한과  
   - 꼬리멘트 **여우 이모지(🦊)** 보장을 수행합니다.

3) `postprocess_bundle()`  
   - (권장) 한 번에 처리하는 편의 함수입니다.  
   - `prepare_alternatives()` + `enforce_response()` 를 호출하여 최종 JSON을 반환합니다.

의존성
------
- 외부 라이브러리 없음(정규식만 사용).
- 토큰화/유사도는 간단한 휴리스틱(공백/한글/영문/숫자 토큰)으로 처리합니다.

주의
----
- 문체 통일(~하기)은 **보수적**으로 적용합니다. 어색한 한국어 생성을 피하기 위해
  특정 어미(하세요/합니다 등)만 안전하게 변환합니다.
- 금칙어 필터는 기본적으로 `*******` 마스킹입니다. 필요 시 동의어 치환을 붙일 수 있습니다.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any

# --------------------------------------------------------------------
# 0) 정규식 준비
# --------------------------------------------------------------------
# 다중 공백을 1칸으로
_WHITESPACE_RE = re.compile(r"\s+")
# ... 또는 …를 통일
_ELLIPSIS_RE = re.compile(r"\u2026|\.{3,}")
# 이모지 대략 범위(완벽하지 않지만 충분)
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]")

# --------------------------------------------------------------------
# 1) 공통 텍스트 유틸
# --------------------------------------------------------------------
def normalize_spaces(text: str) -> str:
    """연속된 공백/개행을 1칸 공백으로 정규화."""
    return _WHITESPACE_RE.sub(" ", (text or "").strip())

def clamp_len(text: str, max_chars: int) -> str:
    """문자열 길이를 max_chars 이하로 자릅니다(말줄임표 … 사용)."""
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"

def ensure_tail_emoji(text: str, emoji: str = "🦊") -> str:
    """문장 끝에 특정 이모지(기본 🦊)가 없으면 붙여 줍니다."""
    text = (text or "").strip()
    if not text.endswith(emoji):
        if text.endswith("."):
            text = text[:-1]
        text = (text + " " + emoji).strip()
    return text

def limit_paragraphs(text: str, max_paragraphs: int = 2) -> str:
    """두 줄 이상 띄어 쓴 단락을 기준으로 잘라 최대 max_paragraphs 단락만 남깁니다."""
    paras = [p.strip() for p in re.split(r"\n{2,}", text or "") if p.strip()]
    return "\n\n".join(paras[:max_paragraphs]) if paras else (text or "").strip()

def limit_emojis(text: str, max_total: int = 2) -> str:
    """
    텍스트의 이모지 개수를 최대 max_total로 제한합니다.
    간단하게 초과분을 제거합니다(표현 보존보다 정책 준수를 우선).
    """
    out = []
    cnt = 0
    for ch in text:
        if _EMOJI_RE.match(ch):
            cnt += 1
            if cnt > max_total:
                continue
        out.append(ch)
    return "".join(out)

# --------------------------------------------------------------------
# 2) 문체 통일(~하기) — 과도한 변환을 피하는 가벼운 휴리스틱
# --------------------------------------------------------------------
def to_verb_noun_style(s: str) -> str:
    """
    가벼운 규칙만 적용해 '~하기/해보기' 형태에 가깝게 다듬습니다.
    - 이미 '하기/해보기/해 두기/켜 두기/쓰기'로 끝나면 그대로 둠
    - '해보세요/하세요/합니다' 등의 종결 어미를 안전하게 '하기/해보기'로 변환
    - 너무 어색해질 위험이 있으면 원문 유지
    """
    s = normalize_spaces(s)
    s = _ELLIPSIS_RE.sub("…", s)

    # 이미 명사형이면 그대로
    if re.search(r"(하기|해보기|해 두기|켜 두기|쓰기)$", s):
        return s

    # 안전한 종결 어미 변환
    replacements = [
        (r"해보세요$", "해보기"),
        (r"해요$", "하기"),
        (r"하세요$", "하기"),
        (r"합니다$", "하기"),
        (r"합니다\.$", "하기"),
        (r"합시다$", "하기"),
        (r"하세요\.$", "하기"),
        (r"하기\.$", "하기"),
    ]
    for pat, rep in replacements:
        if re.search(pat, s):
            return re.sub(pat, rep, s)

    # 이미 '기'로 끝나면 유지(ex. '설정하기', '기록하기')
    if re.search(r"(기)$", s):
        return s

    # 짧은 선언문(…다)인 경우만 부드럽게 변환
    if len(s) <= 20 and s.endswith("다"):
        return s[:-1] + "하기"

    # 그 외는 보수적으로 원문 유지
    return s

# --------------------------------------------------------------------
# 3) 금칙어 필터
# --------------------------------------------------------------------
def filter_forbidden(text: str, forbidden_words: List[str]) -> str:
    """
    금칙어 목록에 있는 단어를 별표(******)로 마스킹합니다.
    - 간단한 substring 치환(단어 경계 판단 없음) — 정책 준수 목적.
    - 필요하면 사전 기반 동의어 치환 로직을 추가할 수 있음.
    """
    out = text
    for w in forbidden_words or []:
        if not w.strip():
            continue
        out = out.replace(w, "*" * len(w))
    return out

# --------------------------------------------------------------------
# 4) 유사도 기반 중복 제거(토큰 자카드)
# --------------------------------------------------------------------
def _tokens(x: str) -> set:
    """한글/영문/숫자 토큰만 뽑아 set으로 변환."""
    return set(re.findall(r"[가-힣A-Za-z0-9]+", x.lower()))

def jaccard_sim(a: str, b: str) -> float:
    """자카드 유사도: 교집합/합집합."""
    A, B = _tokens(a), _tokens(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def dedup_similar(items: List[str], threshold: float = 0.65) -> List[str]:
    """
    의미가 거의 같은 항목을 제거합니다.
    - threshold(기본 0.65) 이상이면 중복으로 판단.
    - 순서대로 보면서, 이미 채택된 항목과의 유사도를 비교합니다.
    """
    out: List[str] = []
    for s in items:
        s_norm = normalize_spaces(s)
        if not s_norm:
            continue
        duplicate = any(jaccard_sim(s_norm, t) >= threshold for t in out)
        if not duplicate:
            out.append(s_norm)
    return out

# --------------------------------------------------------------------
# 5) 대체행동 머지 & 정리
# --------------------------------------------------------------------
def prepare_alternatives(
    llm_items: List[str] | None,
    policy_items: List[str] | None,
    k_min: int = 2,
    k_max: int = 3,
    item_max_chars: int = 90,
    forbidden_words: List[str] | None = None,
) -> List[str]:
    """
    LLM 후보와 정책 후보를 합쳐 '깨끗한' 2~3개 리스트를 만듭니다.
    1) 합치기 → 2) 문체(~하기) → 3) 길이 제한 → 4) 정확 중복 제거 → 5) 의미 중복 제거 → 6) 금칙어 → 7) 개수 보장
    """
    merged = [*(llm_items or []), *(policy_items or [])]

    # 2) 문체/길이/정확 중복 제거
    cleaned = []
    seen = set()
    for s in merged:
        if not s:
            continue
        s = to_verb_noun_style(s)
        s = clamp_len(s, item_max_chars)
        s = normalize_spaces(s)
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)

    # 3) 의미 중복 제거(자카드 유사도)
    cleaned = dedup_similar(cleaned, threshold=0.65)

    # 4) 금칙어 필터(옵션)
    if forbidden_words:
        cleaned = [filter_forbidden(s, forbidden_words) for s in cleaned]

    # 5) 2~3개 보장(부족하면 안전한 기본 항목으로 패딩)
    SAFE_PAD = ["물 한 컵 마시기", "5분 타이머 설정하기", "깊호흡 3회하기"]
    while len(cleaned) < max(2, k_min) and SAFE_PAD:
        s = SAFE_PAD.pop(0)
        if s not in cleaned:
            cleaned.append(s)

    # 6) 최종 개수 컷
    return cleaned[: max(2, min(3, k_max))]

# --------------------------------------------------------------------
# 6) summary/fox_tail 최종 정리
# --------------------------------------------------------------------
def enforce_response(
    summary: str,
    alternatives: List[str],
    fox_tail: str,
    max_paragraphs: int = 2,
    max_emojis: int = 2,
    summary_max_chars: int = 300,
    forbidden_words: List[str] | None = None,
) -> Dict[str, Any]:
    """
    - summary: 공백/단락/길이/이모지/금칙어 처리
    - fox_tail: 공백/이모지 제한 + 꼬리 이모지(🦊) 보장 + 금칙어 처리
    - alternatives: 이미 `prepare_alternatives()`에서 정리된 상태를 사용
    """
    # summary 정리
    summary = normalize_spaces(summary)
    summary = limit_paragraphs(summary, max_paragraphs=max_paragraphs)
    summary = clamp_len(summary, summary_max_chars)
    summary = limit_emojis(summary, max_total=max_emojis)
    if forbidden_words:
        summary = filter_forbidden(summary, forbidden_words)

    # fox_tail 정리
    fox_tail = normalize_spaces(fox_tail or "잠깐 멈추면 더 잘 보여 🦊")
    fox_tail = limit_emojis(fox_tail, max_total=max_emojis)
    fox_tail = ensure_tail_emoji(fox_tail, emoji="🦊")
    if forbidden_words:
        fox_tail = filter_forbidden(fox_tail, forbidden_words)

    return {"summary": summary, "alternatives": alternatives, "fox_tail": fox_tail}

# --------------------------------------------------------------------
# 7) 번들 편의 함수(권장)
# --------------------------------------------------------------------
def postprocess_bundle(
    llm_alternatives: List[str] | None,
    policy_alternatives: List[str] | None,
    summary: str,
    fox_tail: str,
    cfg: Dict[str, Any] | None = None,
    forbidden_words: List[str] | None = None,
) -> Dict[str, Any]:
    """
    prompts.yaml에서 가져온 제약을 적용해 한 번에 후처리합니다.
    - cfg.defaults.list_constraints: {alternatives_min, alternatives_max, alternatives_item_max_chars}
    - cfg.defaults.length_constraints: {max_paragraphs}
    - cfg.defaults.emoji_policy: {max_total}
    - cfg.output_contract.summary_max_chars
    """
    cfg = cfg or {}
    defaults = cfg.get("defaults", {})
    lst = defaults.get("list_constraints", {})
    lc = defaults.get("length_constraints", {})
    emoji = defaults.get("emoji_policy", {})

    item_max = lst.get("alternatives_item_max_chars", 90)
    k_min = lst.get("alternatives_min", 2)
    k_max = lst.get("alternatives_max", 3)
    max_par = lc.get("max_paragraphs", 2)
    max_emj = emoji.get("max_total", 2)
    sum_max = cfg.get("output_contract", {}).get("summary_max_chars", 300) or 300

    final_alts = prepare_alternatives(
        llm_items=llm_alternatives,
        policy_items=policy_alternatives,
        k_min=k_min,
        k_max=k_max,
        item_max_chars=item_max,
        forbidden_words=forbidden_words,
    )
    return enforce_response(
        summary=summary,
        alternatives=final_alts,
        fox_tail=fox_tail,
        max_paragraphs=max_par,
        max_emojis=max_emj,
        summary_max_chars=sum_max,
        forbidden_words=forbidden_words,
    )
