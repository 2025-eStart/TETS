from firebase_admin import firestore

db = firestore.client()

def save_summary_with_id(session_id: str, summary_data: dict) -> dict:
    """
    summaries 컬렉션에 상담 요약을 저장하고, 생성된 문서 ID(counseling_id)를 함께 반환.
    add() 대신 document().set()으로 명시적으로 문서 ID를 만들면
    프론트에 내려준 ID와 실제 저장된 문서가 100% 일치합니다.
    """
    doc = {
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        **summary_data
    }

    # ★ 명시적으로 새 문서 레퍼런스 생성 → set()
    ref = db.collection("summaries").document()
    ref.set(doc)

    counseling_id = ref.id

    # (선택) 디버그 로그
    print("✅ summaries saved:", counseling_id)

    return {
        "session_id": session_id,
        "counseling_id": counseling_id,
        **summary_data
    }