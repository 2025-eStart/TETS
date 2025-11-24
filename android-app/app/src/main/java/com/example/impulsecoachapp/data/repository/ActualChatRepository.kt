//data.repository.ActualChatRepository
package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.data.local.DeviceIdManager
import com.example.impulsecoachapp.data.local.SessionManager
import com.example.impulsecoachapp.data.model.chat.*
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import javax.inject.Inject

class ActualChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val deviceIdManager: DeviceIdManager,
    private val sessionManager: SessionManager
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        val userId = deviceIdManager.getDeviceId()

        return try {
            // 1. 방 번호가 없으면 서버에 요청 (Lazy Initialization)
            if (sessionManager.currentThreadId == null) {
                initializeSession(userId, forceNew = false)
            }

            // 2. 채팅 요청 준비
            val request = ChatRequest(
                userId = userId,
                threadId = sessionManager.currentThreadId!!, // 위에서 초기화 보장됨
                message = text,
                sessionType = sessionManager.currentSessionType
            )

            // 3. 채팅 API 호출
            val response = apiService.sendChatMessage(request)

            // 4. 응답 변환 (DTO -> Domain Model)
            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(response.reply),
                isSessionEnded = response.isEnded,
                currentWeek = response.currentWeek,
                weekTitle = response.weekTitle,
                weekGoals = response.weekGoals
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            // 필요시: sessionManager.clearSession()
            Result.failure(e)
        }
    }

    // [수정됨] 중복 제거 및 initializeSession 재사용
    // 인터페이스 구현체이므로 'override'가 필수입니다.
    override suspend fun startNewGeneralSession(): String {
        val userId = deviceIdManager.getDeviceId()

        // 이미 만들어둔 헬퍼 함수를 재사용하여 코드를 깔끔하게 유지 (DRY 원칙)
        val initRes = initializeSession(userId, forceNew = true)

        return initRes.displayMessage
    }

    // [수정됨] 현재 세션 타입 조회 (인터페이스 구현)
    override fun getCurrentSessionType(): String {
        return sessionManager.currentSessionType
    }

    // 내부 헬퍼 함수: /session/init 호출 및 매니저 업데이트
    // (private으로 숨김)
    private suspend fun initializeSession(userId: String, forceNew: Boolean): InitSessionResponse {
        val request = InitSessionRequest(userId = userId, forceNew = forceNew)
        val response = apiService.initSession(request)

        // 받아온 방 번호와 타입을 메모리에 저장
        sessionManager.updateSession(response.threadId, response.sessionType)

        return response
    }
}
