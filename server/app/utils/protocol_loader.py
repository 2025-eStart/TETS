# app/utils/protocol_loader.py
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List
import yaml

# ---- 필수 키 정의 (BuildPrompt가 기대하는 필드) ----
REQUIRED_KEYS = ["week", "title", "goals", "exit_criteria", "script_steps", "prompt_seed"]

class ProtocolNotFound(Exception):
    pass

# server/app/utils/... 기준으로 server/ 까지 올라간 후 /protocols 고정
SERVER_DIR = Path(__file__).resolve().parents[2]   # .../server
PROTOCOLS_DIR = SERVER_DIR / "protocols"           # .../server/protocols

def _normalize_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]

@lru_cache(maxsize=64)
def load_week_spec(version: str, week: int) -> Dict[str, Any]:
    """
    매우 단순한 로더:
    - 경로: server/protocols/{version}/week{week}.yaml
    - 파일명은 무패딩(week1.yaml, week2.yaml, ...)
    - 형식은 YAML만 지원
    """
    folder = PROTOCOLS_DIR / version
    yml = folder / f"week{int(week)}.yaml"

    if not yml.exists():
        raise ProtocolNotFound(f"Protocol file not found: {yml}")

    with yml.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # 필수 키 점검
    for k in REQUIRED_KEYS:
        if k not in data:
            raise ValueError(f"[protocol {version}/{yml.name}] missing required key: {k}")

    # 타입 정규화
    data["goals"] = _normalize_list(data.get("goals"))
    data["script_steps"] = _normalize_list(data.get("script_steps"))
    data["prompt_seed"] = _normalize_list(data.get("prompt_seed"))
    data["exit_criteria"] = data.get("exit_criteria") or {}

    # week 값 보정(없으면 파일명 기준)
    data["week"] = int(data.get("week") or week)

    return data
