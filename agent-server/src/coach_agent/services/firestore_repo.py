# coach_agent/services/firestore_repo.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from coach_agent.services.base_repo import Repo
from coach_agent.services.firebase_admin_client import get_db
from firebase_admin import firestore
from google.api_core.exceptions import FailedPrecondition, NotFound
from google.cloud.firestore_v1 import FieldFilter

db = get_db()

def _user_doc(uid: str):
    return db.collection("users").document(uid)

def _sessions_col(uid: str):
    return _user_doc(uid).collection("sessions")

def _weekly_key(user_id: str, week: int):
    # 메모리에서는 (user_id, week) 키를 썼지만, Firestore에선 세션 도큐먼트로 일치시킴
    return f"w{week}"

class FirestoreRepo(Repo):
    def get_user(self, user_id: str) -> Dict[str, Any]:
        ref = _user_doc(user_id)
        snap = ref.get()
        if not snap.exists:
            doc = {"user_id": user_id, "current_week": 1, "program_status": "active", "last_seen_at": None}
            ref.set(doc)
            return doc
        return snap.to_dict()

    def upsert_user(self, user_id: str, patch: Dict[str, Any]) -> None:
        _user_doc(user_id).set(patch, merge=True)

    def get_active_weekly_session(self, user_id: str, week: int) -> Optional[Dict[str, Any]]:
        # 디버깅 출력
        print(f"\n🔍 [DB Debug] get_active_weekly_session 시작")
        print(f"   - 검색 조건: User={user_id}, Week={week} (Type: {type(week)})")
        
        # 1. 쿼리 생성
        # session_type 필터는 데이터가 확실히 migration 된 후에 넣는 게 안전할 수 있으나, 
        # 일단 문제 확인을 위해 넣고 테스트합니다.
        try:
            sessions_ref = _sessions_col(user_id)
            q = (sessions_ref
                 .where(filter=FieldFilter("week", "==", int(week)))                        # 현재 주차에 해당하는
                .where(filter=FieldFilter("session_type", "==", "WEEKLY"))                  # WEEKLY 세션 중에서
                .where(filter=FieldFilter("status", "in", ["draft", "active", "paused"])))  # 활성 상태인 것
            
            # 디버깅을 위해 .stream() 결과를 리스트로 변환해 봅니다.
            docs = list(q.stream())
            
            print(f"   - 1차 검색 결과 개수: {len(docs)}")

            # 결과가 없다면, 혹시 'session_type'이나 'week' 타입 문제인지 확인하기 위해
            # 필터를 좀 더 느슨하게 풀어서 다시 검색해봅니다 (로깅용).
            if not docs:
                print("   ⚠️ [DB Debug] 1차 검색 실패. 느슨한 조건으로 재검색 시도...")
                loose_q = sessions_ref.where(filter=FieldFilter("status", "==", "active"))
                loose_docs = list(loose_q.stream())
                print(f"   - Active 상태인 모든 세션 개수: {len(loose_docs)}")
                for d in loose_docs:
                    data = d.to_dict()
                    print(f"     -> 후보 문서 ID: {d.id}")
                    print(f"        Week: {data.get('week')} (Type: {type(data.get('week'))})")
                    print(f"        SessionType: {data.get('session_type')}")
            
            # 정상 로직 진행
            # session_type="WEEKLY" 필터링을 파이썬 레벨에서 수행해서 확실히 확인
            for d in docs:
                data = d.to_dict()
                s_type = data.get("session_type", "UNKNOWN")
                
                print(f"   - 문서 발견! ID: {d.id}, Type: {s_type}")
                
                # session_type이 없거나 WEEKLY인 경우만 리턴 (기존 데이터 호환성 고려)
                if s_type == "WEEKLY" or s_type == "UNKNOWN":
                    data["id"] = d.id
                    print(f"   ✅ [DB Debug] 유효한 세션 반환: {d.id}")
                    return data
                else:
                    print(f"   ❌ [DB Debug] 타입 불일치로 스킵 (Expected WEEKLY, Got {s_type})")

        except Exception as e:
            print(f"   🔥 [DB Error] 쿼리 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()

        print("   🚫 [DB Debug] 적절한 세션을 찾지 못함 -> None 반환")
        return None
        
        '''# 기본 함수
        q = (_sessions_col(user_id)
             .where(filter=FieldFilter("week", "==", int(week)))                         # 현재 주차에 해당하는
             .where(filter=FieldFilter("session_type", "==", "WEEKLY"))                  # WEEKLY 세션 중에서
             .where(filter=FieldFilter("status", "in", ["draft", "active", "paused"])))  # 활성 상태인 것
        try:
            docs = q.order_by("started_at", direction=firestore.Query.DESCENDING).stream()
        except FailedPrecondition:
            docs = q.stream()
        for d in docs:
            it = d.to_dict(); it["id"] = d.id
            return it
        return None
        '''

    ''' # 더이상 사용 안 함
    def create_weekly_session(self, user_id: str, week: int) -> Dict[str, Any]:
        ref = _sessions_col(user_id).document()
        body = {
            "user_id": user_id,
            "week": int(week),
            "status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
            "started_at": firestore.SERVER_TIMESTAMP,
            "last_activity_at": firestore.SERVER_TIMESTAMP,
            "checkpoint": {"step_index": 0},
            "state": {},
            "session_type": "WEEKLY",
        }
        ref.set(body)
        body["id"] = ref.id
        return body
    '''

    
    #  세션 메타데이터 저장/갱신 (메시지 생성 X)
    #     - /session/init 에서 호출 (세션 박제용)
    #     - save_message 에서 호출 (세션 보장용)
    def save_session_info(self, user_id: str, thread_id: str, session_type: str, week: int) -> None:
        """
        세션 문서가 존재하면 -> last_activity_at 갱신
        세션 문서가 없으면 -> 새로 생성 (created_at 포함)
        """
        session_ref = _sessions_col(user_id).document(thread_id)
        
        # 1. 문서 가져오기 (Read)
        snap = session_ref.get()
        
        if snap.exists:
            # (A) 이미 있는 방은 마지막 활동 시간만 갱신
            session_ref.update({
                "last_activity_at": firestore.SERVER_TIMESTAMP
            })
            print(f"   [DB] REPO.save_session_info[A]: Existing session touched: {thread_id}")
        else:
            # (B) 없는 방: 필수 정보 다 채워서 '새로 생성'
            session_ref.set({
                "id": thread_id,
                "user_id": user_id,
                "week": int(week),
                "session_type": session_type,
                "status": "active",
                "created_at": firestore.SERVER_TIMESTAMP,
                "started_at": firestore.SERVER_TIMESTAMP,
                "last_activity_at": firestore.SERVER_TIMESTAMP,
                "checkpoint": {"step_index": 0},
                "state": {},
            })
            print(f"   [DB] REPO.save_session_info[B]: New session created: {thread_id}")
            
    # 일반 메시지 저장 (메시지 생성 O)
    #     - /chat 에서 호출
    def save_message(self, user_id: str, thread_id: str, session_type: str, week: int, role: str, text: str) -> None:
        """
        세션 문서를 확인(없으면 생성)한 후, 메시지를 저장
        """
        # 1. 세션 문서가 준비되었는지 확인
        self.save_session_info(user_id, thread_id, session_type, week)
        
        # 2. 메시지 서브 컬렉션에 추가
        _sessions_col(user_id).document(thread_id).collection("messages").add({
            "user_id": user_id,
            "session_type": session_type,
            "week": week,
            "role": role,
            "text": text,
            "created_at": firestore.SERVER_TIMESTAMP,
        })

    def update_progress(self, user_id: str, week: int, exit_hit: bool) -> None:
        """
        진행도/최근 활동 시간만 갱신.
        주차 진급/프로그램 완료는 mark_session_as_completed가 담당.
        (주차 진급은 mark_session_as_completed 함수 안에서 advance_to_next_week가 호출됨)
        (주의: 이미 active 세션이 존재한다고 가정.)
        """
        # 1. 활성 세션 찾기
        s = self.get_active_weekly_session(user_id, week)
        #  세션이 없으면 절대 새로 만들지 말고, 경고를 띄움
        if not s:
            print(f"🚨 [DB Error] update_progress 실패: {week}주차 활성 세션({user_id})을 찾을 수 없습니다.")
            return

        # 2. 업데이트 수행
        patch = {
            "last_activity_at": firestore.SERVER_TIMESTAMP
        }
        if exit_hit:
            patch["exit_hit_last_turn"] = True

        _sessions_col(user_id).document(s["id"]).set(patch, merge=True)
        print(f"   ✅ [DB] 진행도 업데이트 완료: {s['id']}") # 디버깅 출력

    # --- [1] 상담 완료 여부 기록 ---
    def mark_session_as_completed(self, user_id: str, week: int, completed_at: datetime) -> None:
        """
        현재 주차 세션을 completed로 표시하고,
        user 문서에 last_weekly_session_completed_at을 기록
        """
        # 1. 활성 세션 찾기
        s = self.get_active_weekly_session(user_id, week)
        # 세션이 없으면 중단
        if not s:
            print(f"🚨 [DB Error] 완료 처리 실패: {week}주차 활성 세션({user_id})을 찾을 수 없습니다.")
            return

        # 2. 세션 문서 업데이트 (상태 변경)
        _sessions_col(user_id).document(s["id"]).set({
            "status": "ended",
            "completed_at": completed_at
        }, merge=True)

        # 3. 사용자 문서 업데이트
        _user_doc(user_id).set({
            "last_weekly_session_completed_at": completed_at
        }, merge=True)
        
        # 4. 주차 승급
        self.advance_to_next_week(user_id)

    # --- [2] 상담 완료 후: 주차 진급 & 10주차가 끝나면 program_status:"completed"처리; [1] mark_session_as_completed에서 수행됨 ---
    def advance_to_next_week(self, user_id: str) -> int:
        """
        user.current_week -> +1, 프로그램 완료 처리까지 담당.
        """
        u_ref = _user_doc(user_id)
        snap = u_ref.get()
        if snap.exists:
            u = snap.to_dict()
        else:
            u = {"user_id": user_id, "current_week": 1, "program_status": "active"}

        current_week = int(u.get("current_week", 1))
        next_week = current_week + 1

        if next_week <= 10:
            u_ref.set({"current_week": next_week}, merge=True)
            return next_week
        else:
            # 프로그램 완료 처리
            u_ref.set({"program_status": "completed"}, merge=True)
            return current_week

    # --- [3] 21일 <= 미접속기간 && 이번주 상담 미완료(마지막 상담 완료 날짜+7일 이후): week 1으로 롤백 ---
    def rollback_user_to_week_1(self, user_id: str) -> None:
        """
        21일 이상 미접속 시 프로그램을 week 1부터 다시 시작하게 롤백
        """
        _user_doc(user_id).set({
            "current_week": 1,
            "program_status": "active",
            "last_weekly_session_completed_at": None,
        }, merge=True)
        # 필요하면 sessions 컬렉션도 정리할 수 있음 (여기서는 그대로 둠)

    # --- [4] 24시간 <= 미접속 기간 < 21일 && 이번주 상담 미완료(마지막 상담 완료 날짜+7일 이후): 현재 주차 세션 재시작 ---
    def restart_current_week_session(self, user_id: str, week: int) -> None:
        """
        기존에 Active였던 세션을 종료 처리함 (시간 초과)
        """
        s = self.get_active_weekly_session(user_id, week)
        if s:
            # 기존 세션을 종료 상태로 변경 (더 이상 active로 조회되지 않음)
            # status는 'ended'로 하되, result 필드를 추가해 '중도포기'임을 명시 -> 서랍에서 보이지 않도록 처리
            _sessions_col(user_id).document(s["id"]).update({
                "status": "ended",
                "result": "abandoned",
                "ended_at": firestore.SERVER_TIMESTAMP
            })
            print(f"Session {s['id']} has been closed (abandoned) due to inactivity: 주간 상담 미완료 상태에서 24시간 이상 21일 미만 미접속")

    def last_seen_touch(self, user_id: str) -> None:
        self.upsert_user(user_id, {"last_seen_at": datetime.now(timezone.utc)})
        
    def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """
        user_id에 해당하는 모든 메시지를 Collection Group 쿼리로 가져옵니다.
        (참고: Firestore 콘솔에서 'messages' 컬렉션 그룹에 대한 
         (user_id, created_at) 색인 생성이 필요할 수 있습니다)
        """
        q = (db.collection_group("messages")
             .where(filter=FieldFilter("user_id", "==", user_id))
             .order_by("created_at"))
        
        try:
            docs = q.stream()
            return [d.to_dict() for d in docs]
        except FailedPrecondition as e:
            print(f"FIRESTORE ERROR: 'messages' 컬렉션 그룹에 대한 색인이 필요할 수 있습니다. {e}")
            return []
        except Exception as e:
            print(f"FIRESTORE ERROR: {e}")
            return []
        ''' 과거
        s = self.get_active_weekly_session(user_id, week)
        if not s:
            return []
        
        docs = (_sessions_col(user_id)
                .document(s["id"])
                .collection("messages")
                .order_by("created_at")
                .stream())
        
        return [d.to_dict() for d in docs]
        '''
        
    # --- 요약 함수 2개 ---
    def save_session_summary(self, user_id: str, week: int, summary_text: str) -> None:
        """현재 주차의 'active' 세션에 요약본을 병합(merge)"""
        s = self.get_active_weekly_session(user_id, week)
        if s and s.get("id"):
            try:
                _sessions_col(user_id).document(s["id"]).set({
                    "summary": summary_text,
                    "summary_created_at": firestore.SERVER_TIMESTAMP
                }, merge=True)
            except Exception as e:
                print(f"FIRESTORE ERROR: Failed to save summary for session {s['id']}: {e}")
        else:
            print(f"Warning: No active session found to save summary for user {user_id}, week {week}")

    def get_past_summaries(self, user_id: str, current_week: int) -> List[Dict[str, Any]]:
        """current_week '미만'의 모든 세션에서 'summary' 필드가 있는 문서를 가져옴"""
        q = (_sessions_col(user_id)
             .where(filter=FieldFilter("week", "<", int(current_week)))
             .where(filter=FieldFilter("summary", "!=", None)) # 'summary' 필드가 존재하는 문서만
             .order_by("week"))
        
        summaries = []
        try:
            docs = q.stream()
            for d in docs:
                data = d.to_dict()
                summaries.append({
                    "week": data.get("week"),
                    "session_type": "weekly", # 요약본은 항상 'weekly'
                    "summary": data.get("summary")
                })
            return summaries
        except Exception as e:
            print(f"FIRESTORE ERROR: Failed to get past summaries: {e}")
            return []
           
    # --- 과거 채팅 접근 서랍용 ---
    def get_all_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        users/{uid}/sessions 컬렉션의 모든 문서를 최신순으로 가져옴
        """
        try:
            # created_at 기준 내림차순 (최신이 위로)
            docs = (_sessions_col(user_id)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .stream())
            
            results = []
            for d in docs:
                data = d.to_dict()
                data["id"] = d.id # 문서 ID 포함
                results.append(data)
            return results
            
        except Exception as e:
            print(f"FIRESTORE ERROR (get_all_sessions): {e}")
            return []
        
    # --- 특정 세션의 메시지 기록 가져오기 (서랍 상세용) ---
    def get_session_messages(self, user_id: str, thread_id: str) -> List[Dict[str, Any]]:
        try:
            # sessions/{thread_id}/messages 컬렉션을 시간순 조회
            docs = (_sessions_col(user_id)
                    .document(thread_id)
                    .collection("messages")
                    .order_by("created_at")
                    .stream())
            
            results = []
            for d in docs:
                data = d.to_dict()
                # 필요한 필드만 정리해서 반환
                results.append({
                    "role": data.get("role"),
                    "text": data.get("text"),
                    "created_at": data.get("created_at")
                })
            return results
        except Exception as e:
            print(f"FIRESTORE ERROR (get_session_messages): {e}")
            return []
        
    # --- 현재 주차 세션의 진행 단계(Step Index)를 저장 ---
    def update_checkpoint(self, user_id: str, week: int, step_index: int) -> None:
        print(f"🔍 [DB Debug] 업데이트 시작: User='{user_id}', Week={week}({type(week)}), Step={step_index}")
        
        try:
            sessions_ref = _sessions_col(user_id)
            
            # 1. 쿼리 생성
            # 주의: Firestore에서 숫자가 아닌 문자열로 저장되어 있을 수도 있으니 확인 필요
            query = (sessions_ref
                     .where(filter=FieldFilter("week", "==", week))
                     .where(filter=FieldFilter("status", "==", "active"))
                     .limit(1))
            
            # 2. 쿼리 실행 (리스트로 변환하여 개수 확인)
            docs = list(query.stream())

            # 3. 문서가 없는 경우 (범인은 바로 너!)
            if not docs:
                print(f"🚨 [DB Error] 업데이트 대상을 못 찾았습니다!")
                print(f"   - 검색 조건: week={week}, status='active'")
                print(f"   - 힌트: DB에 week가 문자열 '1'로 되어있지 않나요? 혹은 status가 다른 값인가요?")
                
                # (옵션) 혹시 몰라 문자열로도 한 번 더 찾아봄 (자동 보정 시도)
                # print("   - 문자열 week로 재검색 시도...")
                # query_str = sessions_ref.where(filter=FieldFilter("week", "==", str(week))).limit(1)
                # docs = list(query_str.stream())
                return 

            # 4. 문서가 있는 경우 업데이트
            for doc in docs:
                doc.reference.update({
                    "checkpoint.step_index": step_index, 
                    "last_activity_at": firestore.SERVER_TIMESTAMP
                })
                print(f"✅ [DB Success] 진짜 저장 완료! (Doc ID: {doc.id}) -> Step {step_index}")
                return

        except Exception as e:
            print(f"🔥 [DB Exception] Firestore 에러: {e}")
                        