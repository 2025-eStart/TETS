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
        endSession: Boolean // LangGraph는 서버가 종료를 결정하므로 이 플래그는 사실상 무시되거나 힌트로 사용됨
    ): Result<ChatTurn> {
        return try {
            // 1. 사용자 인증 확인
            val uid = auth.currentUser?.uid ?: "test_user_id" // 로그인 안 되어 있으면 테스트 ID 사용 (개발 편의)

            // 2. 요청 데이터 생성 (LangGraph 표준)
            val requestPayload = LangGraphRequest(
                input = InputData(
                    messages = listOf(MessageData(role = "user", content = text))
                ),
                config = ConfigData(
                    configurable = mapOf("user_id" to uid)
                )
            )

            // 3. API 호출 (/threads/{id}/runs/wait)
            // uid를 스레드 ID로 사용하여 대화 맥락 유지
            val response = apiService.sendMessage(threadId = uid, request = requestPayload)

            // 4. 응답 데이터 파싱
            val values = response.values

            // 4-1. 가장 마지막 AI 메시지 찾기
            val lastMessageContent = values.messages.lastOrNull { it.role == "assistant" }?.content
                ?: "응답을 불러올 수 없습니다."

            // 4-2. ChatMessage 객체 생성
            val assistantMessage = ChatMessage.GuideMessage(
                text = lastMessageContent
            )

            // 4-3. 도메인 모델(ChatTurn)로 변환
            val chatTurn = ChatTurn(
                assistantMessage = assistantMessage,
                isSessionEnded = values.exit, // 서버가 알려준 종료 여부
                homework = null // 현재 프로토콜에는 homework 필드가 명시적으로 없으므로 null (필요시 protocol.goals 활용)
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }
}