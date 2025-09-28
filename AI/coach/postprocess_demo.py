
from postprocess import postprocess_bundle

cfg = {
  "defaults": {
    "list_constraints": {"alternatives_min": 2, "alternatives_max": 3, "alternatives_item_max_chars": 90},
    "length_constraints": {"max_paragraphs": 2},
    "emoji_policy": {"max_total": 2}
  },
  "output_contract": {"summary_max_chars": 300}
}

llm_alts = ["물 한 컵 마시고 5분 산책 후 다시 결정", "장바구니에 담고 24시간 뒤 다시 보기", "깊 호흡 3회 해보세요"]
policy_alts = ["즉석식 + 계란 추가로 10분 내 해결", "비슷한 제품 2개만 남기고 비교표 작성"]

out = postprocess_bundle(
  llm_alternatives=llm_alts,
  policy_alternatives=policy_alts,
  summary="야근 피로와 할인 알림이 겹치며 배달 욕구가 커졌어. 그래서 앱을 열었어.",
  fox_tail="천천히 고르면 충분해요",
  cfg=cfg,
  forbidden_words=["빚을 내서 사"]
)

print(out)
