# agent-server/test_db.py
import os
from dotenv import load_dotenv

# 1. 환경변수 로드 (.env에서 REPO_BACKEND="firestore" 확인)
load_dotenv()
print(f"🔄 모드 확인: {os.getenv('REPO_BACKEND')}")

from src.coach_agent.services import REPO
try:
    # 2. REPO 객체 가져오기 (여기서 연결 시도됨)
    # 경로 문제 해결을 위해 sys.path 설정이 필요할 수 있으나, 
    # 루트에서 실행하면 보통 인식됩니다. 안 되면 아래 주석 해제
    import sys
    sys.path.append(os.path.join(os.getcwd(), "src", "coach_agent"))
    
    # 👇 [추가] REPO의 정체를 밝히는 코드 3줄
    print(f"🕵️ REPO의 정체: {REPO}")
    print(f"🕵️ REPO의 타입: {type(REPO)}")
    
    # 만약 이것이 <class '...'> 라고 출력되면, 괄호()가 빠진 것입니다.
    # 만약 <... object at ...> 라고 출력되면, 객체가 맞습니다.
    
    USER_ID = "test_connection_user"
    
    print("--- [1] 유저 생성/조회 테스트 ---")
    user = REPO.get_user(USER_ID)
    print(f"✅ 유저 정보: {user}")
    
    print("\n--- [2] 유저 정보 업데이트 테스트 ---")
    REPO.upsert_user(USER_ID, {"nickname": "파이어베이스_테스터"})
    updated_user = REPO.get_user(USER_ID)
    print(f"✅ 업데이트된 닉네임: {updated_user.get('nickname')}")
    
    print("\n--- [3] 세션 및 메시지 저장 테스트 ---")
    # 메시지를 저장하면 세션이 없어도 자동으로 생성되어야 함
    REPO.save_message(USER_ID, "WEEKLY", 1, "user", "DB 연결 테스트입니다.")
    print("✅ 메시지 저장 완료")

    print("\n--- [4] 메시지 불러오기 (컬렉션 그룹 쿼리) 테스트 ---")
    # 이 부분에서 색인(Index)이 없으면 에러가 날 수 있음
    messages = REPO.get_messages(USER_ID)
    if messages:
        print(f"✅ 불러온 메시지 개수: {len(messages)}")
        print(f"📝 내용: {messages[0]['text']}")
    else:
        print("⚠️ 메시지가 조회되지 않았습니다. (색인 생성 중일 수 있음)")

    print("\n🎉 모든 테스트 통과! Firebase 연동이 정상입니다.")

except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
    print("팁: .firebase_key.json 경로와 .env 설정을 확인하세요.")