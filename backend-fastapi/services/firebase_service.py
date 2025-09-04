import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 앱이 이미 초기화됐는지 확인 후 실행
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

# Firestore 클라이언트 가져오기
db = firestore.client()

# 기록 저장 함수
def save_chat_log(session_id: str, user_message: str, bot_response: dict):
    print("🔥 Firestore 저장 시도 중...")
    doc = {
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "user_message": user_message,
        "bot_response": bot_response
    }
    try:
        db.collection("chat_logs").add(doc)
        print("✅ Firestore 저장 성공!")
    except Exception as e:
        print("❌ Firestore 저장 실패:", e)

#get-reports api
def get_summaries_by_session(session_id: str):
    try:
        summaries_ref = db.collection("summaries")
        query = summaries_ref \
            .where("session_id", "==", session_id) \
            .where("timestamp", "!=", None) \
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
        docs = query.stream()

        result = []
        for doc in docs:
            data = doc.to_dict()
            result.append({
                "emotion": data.get("emotion"),
                "spending": data.get("spending"),
                "action": data.get("action"),
                "timestamp": data.get("timestamp").isoformat() if data.get("timestamp") else None
            })
        return result

    except Exception as e:
        print("❌ 요약 조회 실패:", e)
        return []
    
def get_spending_by_date(session_id: str, date: str):
    doc_ref = db.collection("spending").document(session_id)
    doc = doc_ref.get()

    if not doc.exists:
        return []

    all_data = doc.to_dict()
    return all_data.get(date, [])

def add_spending_record(session_id: str, date: str, spending_data: dict):
    doc_ref = db.collection("spending").document(session_id)

    doc = doc_ref.get()
    if doc.exists:
        existing_data = doc.to_dict()
    else:
        existing_data = {}

    # 날짜 기준 배열에 항목 추가
    if date in existing_data:
        existing_data[date].append(spending_data)
    else:
        existing_data[date] = [spending_data]

    doc_ref.set(existing_data)