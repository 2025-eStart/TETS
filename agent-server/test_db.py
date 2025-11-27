# agent-server/test_db.py
import os
import sys
from dotenv import load_dotenv

# 1. 환경변수 로드
load_dotenv()
print(f"🔄 모드 확인: {os.getenv('REPO_BACKEND')}")

# 경로 설정 (src 폴더 인식)
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from coach_agent.services import REPO
    
    print(f"🕵️ REPO의 정체: {REPO}")
    # User ID는 테스트용으로 고정
    USER_ID = "test_connection_user"
    TEST_WEEK = 1
    
    # ==========================================
    # [1] 유저 기본 기능 테스트
    # ==========================================
    print("\n--- [1] 유저 생성/조회 테스트 ---")
    user = REPO.get_user(USER_ID)
    print(f"✅ 유저 정보: {user}")
    
    print("\n--- [2] 유저 정보 업데이트 테스트 ---")
    REPO.upsert_user(USER_ID, {"nickname": "파이어베이스_테스터"})
    updated_user = REPO.get_user(USER_ID)
    print(f"✅ 업데이트된 닉네임: {updated_user.get('nickname')}")
    
    # ==========================================
    # [3] (핵심) 세션 및 체크포인트 저장 테스트
    # ==========================================
    print("\n--- [3] 세션 및 체크포인트(Step) 테스트 ---")
    
    # 1. 세션이 없으면 생성, 있으면 가져오기
    session = REPO.get_active_weekly_session(USER_ID, TEST_WEEK)
    if not session:
        print("   -> 활성 세션이 없어서 새로 생성합니다.")
        session = REPO.create_weekly_session(USER_ID, TEST_WEEK)
    
    print(f"   -> 현재 세션 ID: {session.get('id')}")
    print(f"   -> 현재 Status: {session.get('status')} (in_progress여야 함)")
    
    # 2. 데이터 타입 검증 (매우 중요)
    db_week = session.get('week')
    print(f"   -> DB에 저장된 Week 값: {db_week} (Type: {type(db_week)})")
    
    if not isinstance(db_week, int):
        print("   ⚠️ 경고: DB의 Week가 숫자가 아닙니다! 업데이트 실패 원인일 수 있음.")

    # 3. 강제로 Step 1로 업데이트 시도
    TARGET_STEP = 1
    print(f"   -> Step Index를 {TARGET_STEP}로 업데이트 시도...")
    
    # 여기서 우리가 수정한 update_checkpoint 함수가 호출됩니다.
    # (FirestoreRepo에 print문을 넣어뒀다면 여기서 로그가 쫘르륵 떠야 함)
    REPO.update_checkpoint(USER_ID, TEST_WEEK, TARGET_STEP)
    
    # 4. 결과 검증 (다시 DB에서 긁어와서 확인)
    updated_session = REPO.get_active_weekly_session(USER_ID, TEST_WEEK)
    checkpoint = updated_session.get("checkpoint", {})
    saved_step = checkpoint.get("step_index")
    
    print(f"   -> DB에서 다시 조회한 Checkpoint: {checkpoint}")
    
    if saved_step == TARGET_STEP:
        print(f"   🎉 SUCCESS: 체크포인트가 {saved_step}로 정확히 저장되었습니다!")
    else:
        print(f"   💀 FAILURE: 저장 실패! 여전히 {saved_step}입니다.")
        print("      (FirestoreRepo의 쿼리 조건이나 필드명을 다시 확인하세요)")

    # ==========================================
    # [4] 메시지 기능 테스트
    # ==========================================
    print("\n--- [4] 메시지 저장 및 불러오기 테스트 ---")
    REPO.save_message(USER_ID, "WEEKLY", TEST_WEEK, "user", "DB 연결 및 스텝 이동 테스트 중입니다.")
    print("✅ 메시지 저장 완료")

    messages = REPO.get_messages(USER_ID)
    if messages:
        print(f"✅ 불러온 메시지 개수: {len(messages)}")
        print(f"📝 최신 메시지: {messages[-1]['text']}")
    else:
        print("⚠️ 메시지가 조회되지 않았습니다.")

    print("\n✨ 모든 테스트 종료.")

except Exception as e:
    print(f"\n❌ 치명적 에러 발생: {e}")
    import traceback
    traceback.print_exc()