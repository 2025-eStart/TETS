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
import com.google.firebase.auth.FirebaseAuth
import javax.inject.Inject

class ActualChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val deviceIdManager: DeviceIdManager
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        return try {
            // 1. 기기 고유 ID 가져오기 (로그인 불필요)
            val userId = deviceIdManager.getDeviceId()

            val requestPayload = LangGraphRequest(
                input = InputData(
                    messages = listOf(MessageData(type = "human", content = text))
                ),
                config = ConfigData(
                    configurable = mapOf("user_id" to userId) // 가져온 ID 사용
                )
            )

            // 3. API 호출 (/threads/{id}/runs/wait)
            // uid를 스레드 ID로 사용하여 대화 맥락 유지
            val response = apiService.sendMessage(threadId = userId, request = requestPayload)

            // 4. 응답 데이터 파싱
            val values = response.values

            // 4-1. 가장 마지막 AI 메시지 찾기
            val lastMessageContent = values.messages.lastOrNull { it.type == "ai" }?.content
                ?: "응답을 불러올 수 없습니다."

            // 4-2. ChatMessage 객체 생성
            val assistantMessage = ChatMessage.GuideMessage(
                text = lastMessageContent
            )

            // 4-3. 도메인 모델(ChatTurn)로 변환
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