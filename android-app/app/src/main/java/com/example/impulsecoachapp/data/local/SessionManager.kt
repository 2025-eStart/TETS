// data.local.SessionManager
// 서버가 배정해 준 방 번호(thread_id)와 세션 타입을 앱이 켜져 있는 동안 기억해둘 관리자
package com.example.impulsecoachapp.data.local

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SessionManager @Inject constructor() {

    // 현재 배정받은 방 번호
    var currentThreadId: String? = null
        private set

    // 현재 세션 타입 (기본값 WEEKLY)
    var currentSessionType: String = "WEEKLY"
        private set

    // 정보를 업데이트 (initSession 응답 받으면 호출)
    fun updateSession(threadId: String, sessionType: String) {
        this.currentThreadId = threadId
        this.currentSessionType = sessionType
    }

    // 로그아웃이나 앱 초기화 시 호출
    fun clearSession() {
        currentThreadId = null
        currentSessionType = "WEEKLY"
    }
}
