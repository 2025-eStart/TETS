// domain.model.ChatTurn
package com.example.impulsecoachapp.domain.model

import com.example.impulsecoachapp.domain.model.ChatMessage // 기존 모델 재활용

/**
 * ViewModel이 사용할 채팅 응답 도메인 모델
 *
 * @param assistantMessage UI에 표시할 어시스턴트의 메시지
 * @param isSessionEnded 세션 종료 여부
 * @param homework 생성된 숙제 (있을 경우)
 */
data class ChatTurn(
    val assistantMessage: ChatMessage,
    val isSessionEnded: Boolean,
    val homework: Any? = null // Homework 도메인 모델로 변경 가능
)
