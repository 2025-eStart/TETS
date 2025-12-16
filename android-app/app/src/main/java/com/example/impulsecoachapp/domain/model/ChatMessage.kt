// domain.model/ChatMessage
package com.example.impulsecoachapp.domain.model

sealed class ChatMessage {
    // 모든 메시지는 내용을 담고 있어야 함
    abstract val text: String

    // 1. [시스템/가이드] 회색 박스 안내 문구 (예: "상담이 시작되었습니다.")
    data class GuideMessage(override val text: String) : ChatMessage()

    // 2. [유저] 사용자의 입력 (예: "충동이 너무 심해.")
    data class UserResponse(override val text: String) : ChatMessage()

    // 3. [AI 루시] 실제 봇의 답변 (예: "정말 힘드시겠어요. 어떤 상황인가요?")
    data class AssistantMessage(override val text: String) : ChatMessage()
}
