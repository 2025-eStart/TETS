package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.data.model.chat.ChatRequest
import com.example.impulsecoachapp.api.RetrofitClient
import com.example.impulsecoachapp.data.model.chat.ChatMessage
import com.example.impulsecoachapp.ui.screens.chat.ChatRepository

class ActualChatRepository : ChatRepository {
    override suspend fun getNextMessage(userInput: String): ChatMessage {
        return try {
            val response = RetrofitClient.apiService.sendChat(ChatRequest(userInput))
            if (response.isSuccessful) {
                val data = response.body()?.data
                if (data != null) {
                    // 받아온 응답을 앱 내부 메시지 형식으로 변환
                    ChatMessage.GuideMessage(
                        "감정: ${data.emotion}, 소비: ${data.spending}, 추천 행동: ${data.action}"
                    )
                } else {
                    ChatMessage.GuideMessage("응답 데이터가 비어 있어요.")
                }
            } else {
                ChatMessage.GuideMessage("서버 응답 실패 (${response.code()})")
            }
        } catch (e: Exception) {
            ChatMessage.GuideMessage("네트워크 오류: ${e.message}")
        }
    }
}
