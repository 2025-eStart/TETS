
"""
BAS scorer (RI/GDP/RR/IMP schema)
- Loads questionnaire.json in the same folder
- Accepts 1~5 Likert responses with reverse scoring
- Returns means per category (1~5), total mean, and optional 0..100 normalization
"""
from __future__ import annotations
import os, json
from typing import Dict, Any

HERE = os.path.dirname(__file__)
Q_PATH = os.path.join(HERE, "questionnaire.json")

def _load_questionnaire(path: str | None = None) -> dict:
    path = path or Q_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _rev(v: int, reverse: bool) -> int:
    if not (1 <= v <= 5):
        raise ValueError(f"Likert out of range (1..5): {v}")
    return 6 - v if reverse else v

def _norm_0_100(x: float) -> float:
    # x is mean in [1..5]; map to [0..100]
    return round(max(0.0, min(100.0, (x - 1) / 4 * 100)), 2)

def score(responses: Dict[str, int], questionnaire_path: str | None = None) -> Dict[str, Any]:
    """
    responses: {"Q1": 4, "Q2": 3, ...}  # ints 1..5 for ALL items
    returns:
      {
        "mean_total": float,                # 1..5
        "means_by_cat": {"RI": 3.2, ...},   # 1..5
        "norm_total": 0..100,               # optional normalized
        "norm_by_cat": {"RI": 65.0, ...},   # optional normalized
        "counts_by_cat": {"RI": 2, ...}
      }
    """
    q = _load_questionnaire(questionnaire_path)
    items = q["items"]
    cats = {"RI": 0.0, "GDP": 0.0, "RR": 0.0, "IMP": 0.0}
    cnts = {"RI": 0, "GDP": 0, "RR": 0, "IMP": 0}
    total = 0.0
    n = 0
    for it in items:
        qid = it["qid"]
        cat = it["cat"]
        rev = it.get("reverse", False)
        if qid not in responses:
            raise ValueError(f"Missing response for {qid}")
        v = int(responses[qid])
        v = _rev(v, rev)
        cats[cat] += v
        cnts[cat] += 1
        total += v
        n += 1
    means_by_cat = {k: round(cats[k]/cnts[k], 2) if cnts[k] else None for k in cats}
    mean_total = round(total/n, 2) if n else None
    norm_by_cat = {k: _norm_0_100(means_by_cat[k]) if means_by_cat[k] is not None else None for k in cats}
    norm_total = _norm_0_100(mean_total) if mean_total is not None else None
    return {
        "mean_total": mean_total,
        "means_by_cat": means_by_cat,
        "norm_total": norm_total,
        "norm_by_cat": norm_by_cat,
        "counts_by_cat": cnts
    }

if __name__ == "__main__":
    demo = {"Q1":4,"Q2":3,"Q3":4,"Q4":3,"Q5":4,"Q6":2,"Q7":4,"Q8":2,"Q9":4,"Q10":4}
    print(score(demo))
