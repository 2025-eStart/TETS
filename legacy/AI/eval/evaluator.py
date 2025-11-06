
"""
evaluator.py — 시나리오 자동 평가기 (라이트 버전)

- 입력: scenarios.jsonl (각 케이스의 context/expected)
- 모델 연결: call_model(ctx) 함수에 실제 파이프라인 호출을 구현하거나, mock_model을 사용
- 평가: 스키마/정책 준수(개수/단락/이모지/🦊) + 내용 적합성(간단 휴리스틱)
- 출력: JSONL 결과 + HTML 리포트(테이블)

실제 서비스 연동 시:
- call_model(ctx) → inference.pipeline.coach(request) 로 교체
- prompts.yaml 금칙어/제약은 config 로딩 뒤 파라미터로 주입
"""

from __future__ import annotations
import os, json, re, datetime, html
from typing import Dict, Any, List, Tuple

HERE = os.path.dirname(__file__)
REPORT_DIR = os.path.join(HERE, "reports")

# ----------------------------
# 0) 간단한 모형: mock_model
# ----------------------------
def mock_model(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    데모용 고정 규칙 출력:
    - summary: 1~2문장, 공감 한 마디 포함
    - alternatives: BAS/도메인 힌트에 맞는 2~3개 고정 세트
    - fox_tail: 🦊 보장
    """
    mood = ctx.get("mood", "")
    top = ctx.get("spending_top_category", "")
    # 아주 단순한 매핑
    if "배달" in top or "야식" in top:
        alts = ["물 한 컵 마시기", "즉석식으로 10분 내 해결하기"]
    elif "쇼핑" in top:
        alts = ["장바구니에 담고 24시간 뒤 다시 보기", "비슷한 제품 2개만 비교표 작성하기"]
    elif "카페" in top:
        alts = ["집/회사 티백으로 대체하기", "산책 5분 + 텀블러 물 채우기"]
    elif "구독" in top:
        alts = ["지난 30일 사용 시간 확인하기", "체험판으로 먼저 사용해 보기"]
    else:
        alts = ["5분 타이머 설정하기", "깊호흡 3회하기"]

    summary = f"지금 상황이 꽤 부담스러웠겠네. {ctx.get('diary_summary','')[:40]}".strip()
    fox = "잠깐 멈추면 더 잘 보여 🦊"
    return {"summary": summary, "alternatives": alts[:3], "fox_tail": fox}

def call_model(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    실제 연결 지점.
    예: 
      from AI.inference.pipeline import coach
      return coach({...})
    현재는 데모를 위해 mock_model 사용.
    """
    return mock_model(ctx)

# ----------------------------
# 1) 평가 함수들
# ----------------------------
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]")

def count_paragraphs(text: str) -> int:
    paras = [p.strip() for p in re.split(r"\n{2,}", text or "") if p.strip()]
    return max(1, len(paras)) if text else 0

def count_emojis(text: str) -> int:
    return len(EMOJI_RE.findall(text or ""))

def in_range(n: int, lo: int, hi: int) -> bool:
    return lo <= n <= hi

def contains_any(text: str, keywords: List[str]) -> bool:
    t = text or ""
    return any(k in t for k in (keywords or []))

def evaluate_case(ctx: Dict[str, Any], expected: Dict[str, Any], resp: Dict[str, Any], forbidden: List[str] | None = None) -> Dict[str, Any]:
    # 스키마/정책 준수
    alts = resp.get("alternatives", []) or []
    summary = resp.get("summary", "") or ""
    fox = resp.get("fox_tail", "") or ""
    a_ok = in_range(len(alts), expected["alts_count_range"][0], expected["alts_count_range"][1])
    p_ok = count_paragraphs(summary) <= expected["paragraphs_max"]
    e_ok = (count_emojis(summary) + count_emojis(fox)) <= 2
    f_ok = fox.endswith("🦊")
    forb_ok = True
    if forbidden:
        forb_ok = not any(w in (summary + " " + " ".join(alts) + " " + fox) for w in forbidden)

    schema_score = sum([a_ok, p_ok, e_ok, f_ok, forb_ok]) / 5.0

    # 내용 적합성 (아주 라이트한 휴리스틱)
    tone = expected.get("tone_contains", [])
    tone_ok = contains_any(summary, tone) or contains_any(" ".join(alts), tone)

    domain_hint = expected.get("domain_hint", [])
    dom_ok = contains_any(" ".join(alts), ["배달","야식","장바구니","티백","체험판","쿠폰","비교표","산책","타이머"])
    # 위 dom_ok는 간단 키워드로 대체 (실제는 도메인→행동 사전으로 평가 권장)

    content_score = sum([tone_ok, dom_ok]) / 2.0

    # 총점(가중치): 스키마 0.6 + 내용 0.4
    total = round(schema_score * 0.6 + content_score * 0.4, 3)

    return {
        "schema": {
            "alternatives_count_ok": a_ok,
            "paragraphs_ok": p_ok,
            "emoji_budget_ok": e_ok,
            "fox_tail_ok": f_ok,
            "forbidden_ok": forb_ok,
            "score": round(schema_score, 3)
        },
        "content": {
            "tone_ok": tone_ok,
            "domain_ok": dom_ok,
            "score": round(content_score, 3)
        },
        "total": total,
        "response": resp
    }

# ----------------------------
# 2) 실행 진입점
# ----------------------------
def run_eval(scenarios_path: str | None = None, report_dir: str | None = None, forbidden: List[str] | None = None) -> str:
    scenarios_path = scenarios_path or os.path.join(HERE, "scenarios.jsonl")
    report_dir = report_dir or REPORT_DIR
    os.makedirs(report_dir, exist_ok=True)

    results = []
    with open(scenarios_path, "r", encoding="utf-8") as f:
        for line in f:
            sc = json.loads(line)
            ctx = sc["context"]
            expected = sc["expected"]
            resp = call_model(ctx)
            res = evaluate_case(ctx, expected, resp, forbidden=forbidden)
            results.append({"id": sc["id"], "title": sc["title"], "ctx": ctx, "expected": expected, "eval": res})

    # 결과 저장(JSONL)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_jsonl = os.path.join(report_dir, f"results_{ts}.jsonl")
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # HTML 리포트
    out_html = os.path.join(report_dir, f"report_{ts}.html")
    write_html_report(results, out_html)

    return out_html

def write_html_report(results: List[Dict[str, Any]], path: str) -> None:
    rows = []
    for r in results:
        e = r["eval"]
        resp = e["response"]
        schema = e["schema"]; content = e["content"]
        rows.append(f"""
<tr>
  <td>{html.escape(r['id'])}</td>
  <td>{html.escape(r['title'])}</td>
  <td>{e['total']}</td>
  <td>{schema['score']}</td>
  <td>{content['score']}</td>
  <td><pre style='white-space:pre-wrap'>{html.escape(resp.get('summary',''))}</pre></td>
  <td><ul>{"".join(f"<li>{html.escape(a)}</li>" for a in (resp.get('alternatives') or []))}</ul></td>
  <td>{html.escape(resp.get('fox_tail',''))}</td>
</tr>
""")
    html_doc = f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><title>Coach Eval Report</title>
<style>
body{{font-family:system-ui, -apple-system, Segoe UI, Roboto, Noto Sans KR, sans-serif}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;vertical-align:top}}
th{{background:#f7f7f7}}
pre{{margin:0}}
</style>
</head><body>
<h1>Coach Eval Report</h1>
<p>총 케이스: {len(results)}</p>
<table>
<thead>
<tr>
  <th>ID</th><th>Title</th><th>Total</th><th>Schema</th><th>Content</th>
  <th>Summary</th><th>Alternatives</th><th>Fox tail</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)

if __name__ == "__main__":
    out = run_eval(forbidden=["빚을 내서 사", "강제 구매"])
    print("HTML report:", out)
