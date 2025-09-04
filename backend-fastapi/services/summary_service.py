from firebase_admin import firestore

db = firestore.client()

def save_summary(session_id: str, summary_data: dict):
    doc = {
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        **summary_data
    }
    db.collection("summaries").add(doc)

    # 바로 저장한 데이터 내용도 응답에 포함
    return {
        "session_id": session_id,
        **summary_data
    }