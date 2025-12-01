// domain.repository.ChatRepository
package com.example.impulsecoachapp.domain.repository

import com.example.impulsecoachapp.domain.model.ChatTurn

/**
 * 채팅 관련 데이터 처리를 위한 Repository 인터페이스
 */
interface ChatRepository {
    suspend fun sendChatMessage(text: String, endSession: Boolean=false): Result<ChatTurn>

    // 1. 새로운 일반 세션 시작 요청
    suspend fun startNewGeneralSession(): String

    // 2. 현재 세션 타입 조회 (ViewModel이 검사하기 위해)
    fun getCurrentSessionType(): String

    fun getCurrentThreadId(): String?
}
