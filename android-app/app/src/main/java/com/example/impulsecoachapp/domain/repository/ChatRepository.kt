// domain.repository.ChatRepository
package com.example.impulsecoachapp.domain.repository

import com.example.impulsecoachapp.domain.model.ChatTurn

/**
 * 채팅 관련 데이터 처리를 위한 Repository 인터페이스
 */
interface ChatRepository {

    // ... (예: 이전 대화 내역 불러오기 함수) ...

    /**
     * 사용자 메시지를 전송하고 어시스턴트의 응답을 받습니다.
     * @param text 사용자가 입력한 텍스트
     * @param endSession 이 호출로 세션을 종료할지 여부
     */
    suspend fun sendChatMessage(text: String, endSession: Boolean = false): Result<ChatTurn>
}