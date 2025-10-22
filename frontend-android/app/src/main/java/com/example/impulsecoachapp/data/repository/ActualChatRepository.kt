package com.example.impulsecoachapp.repository

import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.data.model.chat.ChatMessage
import com.example.impulsecoachapp.data.model.chat.ChatRequest // <-- 'Next' 제거
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.ui.screens.chat.ChatRepository
import com.google.firebase.auth.FirebaseAuth // Firebase Auth 사용 가정

class ActualChatRepository(
    private val apiService: ApiService,
    private val auth: FirebaseAuth // DI 또는 직접 생성
) : ChatRepository {

    override suspend fun sendChatMessage(text: String, endSession: Boolean = false): Result<ChatTurn> {
        return try {
            val uid = auth.currentUser?.uid
            if (uid == null) {
                return Result.failure(Exception("사용자가 인증되지 않았습니다."))
            }

            // 1. API 요청 객체 생성 (클래스 이름 변경)
            val request = ChatRequest( // <-- 'Next' 제거
                uid = uid,
                text = text,
                end = endSession
            )

            // 2. API 호출
            val response = apiService.chatNext(request)

            // 3. API 응답을 UI용 도메인 모델로 매핑

            // [중요!] 백엔드 담당자에게 'reply' 객체 중 어떤 필드가
            // 실제 말풍선에 표시될 텍스트인지 확인해야 합니다.
            // 여기서는 'reply.action'을 텍스트로 가정합니다.
            val assistantMessageText = response.reply.action

            val assistantMessage = ChatMessage(
                text = assistantMessageText,
                role = "assistant", // 또는 "model"
                timestamp = System.currentTimeMillis() // 또는 서버 시간 사용
            )

            val chatTurn = ChatTurn(
                assistantMessage = assistantMessage,
                isSessionEnded = response.isEnded,
                homework = response.homework
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            // 네트워크 오류, JSON 파싱 오류 등 처리
            Result.failure(e)
        }
    }
}
