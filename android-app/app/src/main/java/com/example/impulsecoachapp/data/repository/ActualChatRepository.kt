//data.repository.ActualChatRepository
//LangGraph 서버의 응답 구조(values -> messages 리스트)에서 **가장 마지막 메시지(AI의 답변)**를 추출
package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.data.model.chat.ConfigData
import com.example.impulsecoachapp.data.model.chat.InputData
import com.example.impulsecoachapp.data.model.chat.LangGraphRequest
import com.example.impulsecoachapp.data.model.chat.MessageData
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import com.google.firebase.auth.FirebaseAuth
import javax.inject.Inject

class ActualChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val auth: FirebaseAuth
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        return try {
            val uid = auth.currentUser?.uid ?: "test_user_id"

            // 1. 요청 (LangGraph 표준)
            val requestPayload = LangGraphRequest(
                input = InputData(messages = listOf(MessageData("user", text))),
                config = ConfigData(configurable = mapOf("user_id" to uid))
            )

            val response = apiService.sendMessage(uid, requestPayload)
            val values = response.values

            // 2. 마지막 AI 응답 추출
            val lastMessageContent = values.messages.lastOrNull { it.role == "assistant" }?.content
                ?: "..." // 응답이 없을 경우 처리

            // 3. Domain 모델 매핑 (업데이트됨)
            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(lastMessageContent),
                isSessionEnded = values.exit,

                // ★ 추가된 메타 데이터 매핑
                currentWeek = values.currentWeek,
                weekTitle = values.protocol?.title ?: "상담", // 제목이 없으면 기본값
                weekGoals = values.protocol?.goals ?: emptyList() // 목표 리스트
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }
}