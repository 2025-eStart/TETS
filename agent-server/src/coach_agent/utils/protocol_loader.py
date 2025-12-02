# coach_agent/utils/protocol_loader.py
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List
from coach_agent.graph.state import State
import yaml


class ProtocolNotFound(Exception):
    pass


VERSION = "v2"
COACH_AGENT_DIR = Path(__file__).resolve().parent.parent   # .../src/coach_agent
PROTOCOLS_DIR = COACH_AGENT_DIR / "protocols"          # .../src/coach_agent/protocols
folder = PROTOCOLS_DIR / VERSION
TECHNIQUE_CATALOG_PATH = folder / "techniques.yaml"

def _normalize_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]

#-----------------------------
# 1) 주차별 프로토콜 로더
# -----------------------------
def _safe_list(value: Any) -> List[Any]:
    """None 등 들어와도 항상 list 로 만들어주는 작은 유틸."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    # 실수로 문자열이 들어와도 한 원소짜리 리스트로 감싸기
    return [value]


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}



@lru_cache(maxsize=64)
def load_protocol_spec(week: int) -> Dict[str, Any]:
    """
    weekN.yaml 을 읽어서, 내부에서 쓰기 좋은 형태로 정규화한 dict 를 반환.
    - 필수/선택 필드 모두 안전하게 기본값 처리
    - core_task.tags → core_task_tags 로 평탄화
    - 경로: agent-server/src/protocols/{version}/week{week}.yaml
    - 파일명은 무패딩(week1.yaml, week2.yaml, ...)
    - 형식은 YAML만 지원
    """
    
    yml = folder / f"week{int(week)}.yaml"

    if not yml.exists():
        raise ProtocolNotFound(f"Protocol file not found: {yml}")

    with yml.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # 1) 기본 메타
    title = raw.get("title")
    agenda = raw.get("agenda")
    description = raw.get("description")

    # 2) 세션 목표 / core_task
    session_goal = raw.get("session_goal")

    core_task = _safe_dict(raw.get("core_task"))
    core_task_description = core_task.get("description")
    core_task_tags = _safe_list(core_task.get("tags"))

    # 3) 성공 기준
    success_criteria = _safe_list(raw.get("success_criteria"))

    # 4) 기법 관련
    allowed_techniques = _safe_list(raw.get("allowed_techniques"))
    blocked_techniques = _safe_list(raw.get("blocked_techniques"))

    # 5) 제약 조건
    constraints_raw = _safe_dict(raw.get("constraints"))
    # 기본값 보정
    # min_turns = constraints_raw.get("min_turns", 3)
    max_turns = constraints_raw.get("max_turns", 12)
    exit_policy = _safe_dict(constraints_raw.get("exit_policy"))

    constraints: Dict[str, Any] = {
        # "min_turns": min_turns,
        "max_turns": max_turns,
        "exit_policy": exit_policy,
    }

    # 6) 과제
    homework = _safe_dict(raw.get("homework"))

    return {
        "week": raw.get("week", week),
        "title": title,
        "agenda": agenda,
        "description": description,
        "session_goal": session_goal,
        "core_task": {
            "description": core_task_description,
            "tags": core_task_tags,
        },
        "core_task_tags": core_task_tags,
        "success_criteria": success_criteria,
        "allowed_techniques": allowed_techniques,
        "blocked_techniques": blocked_techniques,
        "constraints": constraints,
        "homework": homework,
    }


#-----------------------------
# 2) 개입 방법 로더
# -----------------------------
@lru_cache(maxsize=1)
def load_techniques_catalog() -> Dict[str, Dict[str, Any]]:
    """
    intervention.yaml 에 정의된 CBT 기법 카탈로그를 로드하여
    id → 기법 메타데이터 dict 로 반환.

    예상 YAML 구조:
    - id: "thought_record"
      level: "intervention" | "technique"
      name: "..."
      description: "..."
      typical_targets: [...]
      good_for_focus: [...]
      rag_tags: [...]
      # 필요시 추가 필드들

    반환값 예:
    {
      "thought_record": {...},
      "socratic_questioning": {...},
      ...
    }
    """

    path = TECHNIQUE_CATALOG_PATH
    if not path.exists():
        raise FileNotFoundError(f"[protocol_loader] 기법 카탈로그 파일을 찾을 수 없습니다: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []

    if not isinstance(raw, list):
        raise ValueError("[protocol_loader] intervention.yaml 최상위 구조는 list 여야 합니다.")

    catalog: Dict[str, Dict[str, Any]] = {}

    for item in raw:
        if not isinstance(item, dict):
            continue
        tech_id = item.get("id")
        if not tech_id:
            continue

        # 필요 시 기본값 보정
        level = item.get("level", "technique")
        name = item.get("name", tech_id)
        description = item.get("description", "")

        typical_targets = _safe_list(item.get("typical_targets"))
        good_for_focus = _safe_list(item.get("good_for_focus"))
        rag_tags = _safe_list(item.get("rag_tags"))

        normalized = {
            "id": tech_id,
            "level": level,
            "name": name,
            "description": description,
            "typical_targets": typical_targets,
            "good_for_focus": good_for_focus,
            "rag_tags": rag_tags,
            # 기타 필드 그대로 유지
        }

        # 원본 item 의 나머지 필드도 덮어쓰기 없이 병합
        for k, v in item.items():
            if k not in normalized:
                normalized[k] = v

        catalog[tech_id] = normalized

    return catalog

#-----------------------------
# 3) 일반 FAQ 세션용, homework만 로드
# -----------------------------
def load_homework_block_for_week(week: int) -> str:
    """
    프로토콜 원문 텍스트에서
    '# ===========================' / '# 4) Homework' 이후의 내용을
    전부 잘라서 반환한다.

    전제:
      - 파일은 YAML이지만, 우리가 필요한 건 '# 4) Homework' 이후의
        원문 텍스트(주석/마크다운) 그대로이다.
      - '그 이후 전부가 homework' 라는 네 설명에 맞춰 구현.
    """
    path = folder / f"week{week}.yaml"

    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[Protocol] Homework 파일을 찾을 수 없습니다: {path}")
        return ""

    lines = raw_text.splitlines(keepends=False)

    in_homework = False
    homework_lines: list[str] = []

    HOMEWORK_MARKER = "# 4) Homework"
    for line in lines:
        # 시작 지점: '# 4) Homework'가 포함된 줄
        if not in_homework and HOMEWORK_MARKER in line:
            in_homework = True
            # '이후의 내용 전부'가 homework이므로,
            # 이 줄 바로 다음 줄부터 homework로 취급
            continue

        if in_homework:
            # 네 설명 기준: 끝나는 지점은 정의 안 되어 있고,
            # 파일 끝까지가 homework이므로 별도 종료 조건은 두지 않음
            homework_lines.append(line)

    if not homework_lines:
        print(f"[Protocol] week={week} 프로토콜에서 Homework 섹션을 찾지 못했습니다.")
        return ""

    homework_text = "\n".join(homework_lines).strip()
    return homework_text