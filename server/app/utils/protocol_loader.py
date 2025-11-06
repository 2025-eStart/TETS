# app/utils/protocol_loader.py
from __future__ import annotations          # 앞으로 나올 타입 힌트를 문자열 없이 사용할 수 있게(순환 참조 등 방지)
import re                                   # 종료 기준에서 정규식 패턴 매칭을 위해 사용
from functools import lru_cache             # 프로토콜 파일을 자주 읽는 걸 캐시해 I/O 비용 감소
from pathlib import Path                    # 파일 경로를 OS 독립적으로 다루기 위해
from typing import Dict, Any, List          # 타입 힌트용

import yaml                                 # YAML 파일 파싱

# BuildPrompt가 기대하는 필드:
# ["week", "title", "goals", "exit_criteria", "script_steps", "prompt_seed"]
REQUIRED_KEYS = ["week", "title", "goals", "exit_criteria", "script_steps", "prompt_seed"]
# ↑ 주차 스펙이 반드시 가져야 할 키 목록 (없으면 에러로 빠짐)

# app/ 기준으로 안전하게 경로 계산
BASE_DIR = Path(__file__).resolve().parents[1]   # 현재 파일(app/utils/…) 기준 상위 폴더(app/) 경로 계산
PROTOCOLS_DIR = BASE_DIR / "protocols"           # app/protocols 폴더 경로를 미리 만들어 둠

class ProtocolNotFound(Exception):
    pass
# ↑ 프로토콜 파일이 없을 때 명시적으로 던질 커스텀 예외

def _normalize_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]
# ↑ 스펙에서 리스트로 기대하는 필드(goals, script_steps, prompt_seed)가
#   단일 문자열로 들어와도 안전하게 리스트[str]로 정규화

@lru_cache(maxsize=64)
def load_week_spec(version: str, week: int) -> Dict[str, Any]:
    """
    YAML 스펙 로더.
    경로: app/protocols/{version}/weekNN.yaml
    - 필수 키 검증
    - list 타입 필드(goals, script_steps, prompt_seed) 정규화
    """
    folder = PROTOCOLS_DIR / version                 # 특정 버전(예: v1) 폴더
    yml = folder / f"week{week:02d}.yaml"            # week01.yaml 같은 파일 경로 생성

    if not yml.exists():
        raise ProtocolNotFound(f"Protocol file not found: {yml}")
    # ↑ 파일이 없으면 예외 발생 (PickWeek 노드에서 잡히거나 상위로 전파)

    with yml.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # ↑ YAML을 파싱해서 dict로 로드. 비어 있으면 {}로 대체

    # 필수 키 존재 확인
    for k in REQUIRED_KEYS:
        if k not in data:
            raise ValueError(f"[protocol {version}/week{week:02d}] missing required key: {k}")
    # ↑ BuildPrompt가 의존하는 필드들이 모두 있는지 확인. 없으면 즉시 에러

    # 타입 정규화 (BuildPrompt와의 계약)
    data["goals"] = _normalize_list(data.get("goals"))
    data["script_steps"] = _normalize_list(data.get("script_steps"))
    data["prompt_seed"] = _normalize_list(data.get("prompt_seed"))
    # ↑ 리스트로 기대하는 필드를 모두 리스트[str]로 보정
    #   (나중에 BuildPrompt가 join() 등을 안전하게 수행)

    # optional 기본값
    data["exit_criteria"] = data.get("exit_criteria") or {}
    # ↑ exit_criteria가 비어 있으면 {}로 (CheckExitOrPause에서 None 문제 방지)

    return data
    # ↑ 최종적으로 정규화된 스펙 dict 반환 → PickWeek 노드가 s.protocol에 넣음


# ----------------- Exit criteria evaluation -----------------

def _hit_patterns(text: str, patterns: List[str]) -> int:
    hits = 0
    for pat in patterns:
        try:
            if re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE):
                hits += 1
        except re.error:
            # 정규식이 아니면 부분 문자열로 처리
            if pat.lower() in text.lower():
                hits += 1
    return hits
# ↑ 문자열 text에 대해 주어진 patterns 각각이 매칭되는지 체크해서 “맞은 개수”를 반환
#   - 올바른 정규식이면 re.search로, 잘못된 정규식(혹은 단순 키워드)이면 부분 문자열로 판단
#   - 대소문자 구분 없이 멀티라인으로 검색


def meets_exit_criteria(llm_output: str | None, criteria: Dict[str, Any]) -> bool:
    """
    구조화된 종료 규칙을 평가.
    지원 형태(둘 다 optional, 있으면 적용):

    exit_criteria:
      required:                 # AND 블록
        patterns: ["상황","감정","사고"]
        min_hits: 3
      when_any:                 # OR 블록 (여러 그룹 중 하나라도 충족)
        - patterns: ["근거","반증"]
          min_hits: 2
        - llm_signals: ["soat_captured","goals_aligned"]
          min_true: 2

    * patterns: 응답 텍스트에 대한 정규식/부분문자열 매칭
    * llm_signals: 지금은 텍스트 토큰 매칭으로 프록시(요약 구조 연동 시 교체 가능)

    둘 다 비어 있으면 False.
    """
    text = (llm_output or "").strip()        # None 방지 및 앞뒤 공백 제거
    if not text or not criteria:
        return False                         # 응답이 비었거나 기준이 없으면 종료 불가

    # required (AND)
    req = criteria.get("required")           # 필수(AND) 블록을 꺼냄
    if req:
        pats = req.get("patterns", [])       # 필수 패턴 목록
        min_hits = int(req.get("min_hits", len(pats))) if pats else 0
        # ↑ min_hits가 지정돼 있지 않으면 패턴 개수 전부 맞아야 통과
        if pats and _hit_patterns(text, pats) < min_hits:
            return False                     # 필수 조건을 못 채우면 바로 실패

    # when_any (OR)
    groups = criteria.get("when_any", [])    # 선택(OR) 그룹들
    if groups:
        for g in groups:
            # 패턴 기반 그룹
            if "patterns" in g:
                pats = g.get("patterns", [])
                min_hits = int(g.get("min_hits", len(pats))) if pats else 0
                if _hit_patterns(text, pats) >= min_hits:
                    return True              # 그룹 하나라도 조건 충족하면 종료 가능

            # 요약 신호 기반 그룹(토큰 매칭)
            if "llm_signals" in g:
                sigs = g.get("llm_signals", [])
                min_true = int(g.get("min_true", len(sigs))) if sigs else 0
                if _hit_patterns(text, sigs) >= min_true:
                    return True              # 신호 토큰 매칭으로도 통과 가능

        # 어떤 그룹도 만족 못함
        return False

    # when_any가 없고 required만 있으면 required 통과로 종료 허용
    return bool(req)
