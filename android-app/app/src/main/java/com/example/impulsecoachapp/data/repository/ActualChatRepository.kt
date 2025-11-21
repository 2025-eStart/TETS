//data.repository.ActualChatRepository
//LangGraph 서버의 응답 구조(values -> messages 리스트)에서 **가장 마지막 메시지(AI의 답변)**를 추출
package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.data.local.DeviceIdManager
import com.example.impulsecoachapp.data.model.chat.ConfigData
import com.example.impulsecoachapp.data.model.chat.InputData
import com.example.impulsecoachapp.data.model.chat.LangGraphRequest
import com.example.impulsecoachapp.data.model.chat.MessageData
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import javax.inject.Inject

class ActualChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val deviceIdManager: DeviceIdManager // [수정] FirebaseAuth 대신 DeviceIdManager 주입
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        return try {
            // 1. [수정] 기기 고유 ID 가져오기 (로그인 불필요)
            val userId = deviceIdManager.getDeviceId()

            val requestPayload = LangGraphRequest(
                input = InputData(
                    messages = listOf(MessageData(role = "user", content = text))
                ),
                config = ConfigData(
                    configurable = mapOf("user_id" to userId) // 가져온 ID 사용
                )
            )

            // ... (이하 로직 동일) ...
            val response = apiService.sendMessage(threadId = userId, request = requestPayload)
            val values = response.values

            val lastMessageContent = values.messages.lastOrNull { it.role == "assistant" }?.content
                ?: "..."

            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(lastMessageContent),
                isSessionEnded = values.exit,
                currentWeek = values.currentWeek,
                weekTitle = values.protocol?.title ?: "상담",
                weekGoals = values.protocol?.goals ?: emptyList()
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }
}
