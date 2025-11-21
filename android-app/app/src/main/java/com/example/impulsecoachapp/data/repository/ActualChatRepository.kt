//data.repository.ActualChatRepository
package com.example.impulsecoachapp.data.repository
import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.data.model.chat.ChatRequest
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import com.google.firebase.auth.FirebaseAuth
import java.util.Date

class ActualChatRepository(
    private val apiService: ApiService,
    private val auth: FirebaseAuth
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean // 인터페이스를 따르도록 기본값 제거
    ): Result<ChatTurn> {
        return try {
            val uid = auth.currentUser?.uid
            if (uid == null) {
                return Result.failure(Exception("사용자가 인증되지 않았습니다."))
            }

            val request = ChatRequest(
                uid = uid,
                text = text,
                end = endSession
            )

            val response = apiService.chatNext(request)

            // 백엔드의 응답 텍스트 추출
            val assistantMessageText = response.reply.action

            // 3. [중요!] ChatMessage.Assistant 하위 클래스로 생성
            val assistantMessage = ChatMessage.GuideMessage(
                text = assistantMessageText
            )

            val chatTurn = ChatTurn(
                assistantMessage = assistantMessage,
                isSessionEnded = response.isEnded,
                homework = response.homework
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}