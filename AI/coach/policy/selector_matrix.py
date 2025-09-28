
from __future__ import annotations
import os, json, random
from typing import Dict, List, Any

HERE = os.path.dirname(__file__)

def load_matrix(path: str | None = None) -> dict:
    path = path or os.path.join(HERE, "alternatives_matrix.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_by_bas_type(
    bas_means_by_cat: Dict[str, float],
    context: Dict[str, Any] | None = None,
    matrix: dict | None = None,
    k_min: int = 2,
    k_max: int = 3
) -> List[str]:
    """
    BAS 평균 점수(1..5) 중 높은 유형을 골라 그 유형에 맞는 도메인 → 행동을 추천.
    context 예: {"setting":"home","mood":"피곤"} (현재는 가벼운 랜덤 섞기만)
    """
    M = matrix or load_matrix()
    # 1) BAS 유형 우선순위
    ordered = sorted(bas_means_by_cat.items(), key=lambda kv: kv[1], reverse=True)
    # 2) 각 BAS 유형 → 도메인 순서 → (by_bas + common) 후보 생성
    cands: List[str] = []
    used = set()
    for bas_type, _ in ordered:
        domains = M["bas_to_domains"].get(bas_type, [])
        for dom in domains:
            dom_conf = M["domains"].get(dom, {})
            # 유형 맞춤(by_bas) + 공통(common) 합치기
            by_bas = dom_conf.get("by_bas", {}).get(bas_type, [])
            common = dom_conf.get("common", [])
            for s in by_bas + common:
                if s not in used:
                    used.add(s); cands.append(s)
            if len(cands) >= 12:
                break
        if len(cands) >= 12:
            break
    # 3) 컨텍스트 가중치(간단화): 현재는 랜덤 섞기
    random.shuffle(cands)
    k = max(k_min, min(k_max, 3))
    return cands[:k]
