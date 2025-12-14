package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.api.ApiService
import com.example.impulsecoachapp.data.local.*
import com.example.impulsecoachapp.data.model.chat.*
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.model.Homework
import com.example.impulsecoachapp.domain.repository.ChatRepository
import javax.inject.Inject

class ActualChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val deviceIdManager: DeviceIdManager,
    private val sessionManager: SessionManager,
    private val homeworkStorage: HomeworkStorage
) : ChatRepository {

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        val userId = deviceIdManager.getDeviceId()

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

            var domainHomework: Homework? = null

            if (response.homework != null) {
                domainHomework = Homework(
                    description = response.homework.description,
                    examples = response.homework.examples
                )
                homeworkStorage.saveHomework(domainHomework)
            }

            val chatTurn = ChatTurn(
                assistantMessage = ChatMessage.GuideMessage(response.reply),
                isSessionEnded = response.isEnded,
                currentWeek = response.currentWeek,
                weekTitle = response.weekTitle,
                weekGoals = response.weekGoals ?: emptyList(),
                homework = domainHomework
            )

            Result.success(chatTurn)

        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

    // 리마인더: 일일 과제 알림용 과제 객체 가져오기
    fun getStoredHomework(): Homework? {
        return homeworkStorage.getHomework()
    }
    // 리마인더: 알림에 띄울 텍스트가 필요할 때 사용하는 헬퍼
    fun getStoredHomeworkAsNotificationText(): String {
        val homework = homeworkStorage.getHomework() ?: return homeworkStorage.getDefaultMessage()

        // 알림에는 description과 예시 1개 정도만 요약해서 보여주거나, description만 보여줌
        return "${homework.description}\n(예시: ${homework.examples.firstOrNull() ?: "없음"})"
    }

    // 앱 진입 시 봇을 먼저 깨우는 함수
    suspend fun startSession(forceNew: Boolean = false): Result<ChatTurn> {
        val userId = deviceIdManager.getDeviceId()

        //  안전장치를 추가 (앱 켤 때 실행되는 곳이라 더 중요함)
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
        // 목록 가져오기 실패 방지
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

        //  앱 켜자마자 실행되는 함수라 여기도 필수
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
    // 서랍에서 다른 세션으로 갈아탈 때, 세션 매니저 정보를 갱신하는 함수
    fun updateCurrentSessionInfo(threadId: String, sessionType: String) {
        sessionManager.updateSession(threadId, sessionType)
    }

    // 상담 진행도 리셋하고 1주차부터 다시 시작하기
    override suspend fun resetSession(): Result<InitSessionResponse> {
        val userId = deviceIdManager.getDeviceId()
        if (userId.isBlank()) {
            return Result.failure(IllegalStateException("유저 ID가 없습니다."))
        }

        return try {
            // 1) 서버 리셋 호출 → 새 thread 발급
            val initResponse = apiService.resetSession(ResetRequest(userId))

            // 2) 로컬 세션 상태 동기화 (새 채팅방으로 전환)
            sessionManager.updateSession(
                threadId = initResponse.threadId,
                sessionType = initResponse.sessionType
            )

            Result.success(initResponse)
        } catch (e: Exception) {
            e.printStackTrace()
            Result.failure(e)
        }
    }

}
