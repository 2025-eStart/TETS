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

        // ✅ [수정됨] 오타 수정 (failrue -> failure)
        if (userId.isBlank()){
            return Result.failure(IllegalStateException("유저 ID가 생성되지 않았습니다."))
        }

        return try {
            if (sessionManager.currentThreadId == null) {
                initializeSession(userId, forceNew = false)
            }

            val request = ChatRequest(
                userId = userId,
                threadId = sessionManager.currentThreadId!!,
                message = text,
                sessionType = sessionManager.currentSessionType
            )

            val response = apiService.sendChatMessage(request)

            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(response.reply),
                isSessionEnded = response.isEnded,
                currentWeek = response.currentWeek,
                weekTitle = response.weekTitle,
                weekGoals = response.weekGoals ?: emptyList(),
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

    // 앱 진입 시 봇을 먼저 깨우는 함수
    suspend fun startSession(forceNew: Boolean = false): Result<ChatTurn> {
        val userId = deviceIdManager.getDeviceId()

        // ✅ [추천] 여기에도 안전장치를 추가하세요 (앱 켤 때 실행되는 곳이라 더 중요함)
        if (userId.isBlank()){
            return Result.failure(IllegalStateException("유저 ID가 생성되지 않았습니다."))
        }

        return try {
            if (sessionManager.currentThreadId == null || forceNew) {
                initializeSession(userId, forceNew = forceNew)
            }

            val request = ChatRequest(
                userId = userId,
                threadId = sessionManager.currentThreadId!!,
                message = "__init__",
                sessionType = sessionManager.currentSessionType
            )

            val response = apiService.sendChatMessage(request)

            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(response.reply),
                isSessionEnded = response.isEnded,
                currentWeek = response.currentWeek,
                weekTitle = response.weekTitle,
                weekGoals = response.weekGoals ?: emptyList()
            )
            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

    override suspend fun startNewGeneralSession(): String {
        val userId = deviceIdManager.getDeviceId()
        // 여기는 initializeSession 내부에서 호출되므로 별도 처리 안 해도 됨 (혹은 initializeSession 안에서 검사해도 됨)
        val initRes = initializeSession(userId, forceNew = true)
        return initRes.displayMessage
    }

    override fun getCurrentSessionType(): String {
        return sessionManager.currentSessionType
    }

    override fun getCurrentThreadId(): String? {
        return sessionManager.currentThreadId
    }

    suspend fun getHistoryList(): Result<List<SessionSummary>> {
        val userId = deviceIdManager.getDeviceId()
        // ✅ [선택] 목록 가져오기 실패 방지
        if (userId.isBlank()) return Result.failure(IllegalStateException("No User ID"))

        return try {
            val list = apiService.getSessions(userId)
            Result.success(list)
        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

    suspend fun getSessionHistory(threadId: String): Result<List<ChatMessage>> {
        val userId = deviceIdManager.getDeviceId()
        if (userId.isBlank()) return Result.failure(IllegalStateException("No User ID"))

        return try {
            val responseList = apiService.getSessionHistory(userId, threadId)
            val chatMessages = responseList.map { item ->
                when (item.role.lowercase()) {
                    "user", "human" -> ChatMessage.UserResponse(item.text)
                    "ai", "assistant", "bot" -> ChatMessage.GuideMessage(item.text)
                    else -> ChatMessage.GuideMessage(item.text)
                }
            }
            Result.success(chatMessages)
        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

    private suspend fun initializeSession(userId: String, forceNew: Boolean): InitSessionResponse {
        val request = InitSessionRequest(userId = userId, forceNew = forceNew)
        val response = apiService.initSession(request)
        sessionManager.updateSession(response.threadId, response.sessionType)
        return response
    }

    suspend fun initOrRestoreSession(forceNew: Boolean = false): Result<InitSessionResponse> {
        val userId = deviceIdManager.getDeviceId()

        // ✅ [추천] 앱 켜자마자 실행되는 함수라 여기도 필수
        if (userId.isBlank()){
            return Result.failure(IllegalStateException("유저 ID가 생성되지 않았습니다."))
        }

        return try {
            val req = InitSessionRequest(
                userId = userId,
                forceNew = forceNew
            )
            val res = apiService.initSession(req)
            sessionManager.updateSession(
                res.threadId,
                res.sessionType
            )
            Result.success(res)
        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }
}