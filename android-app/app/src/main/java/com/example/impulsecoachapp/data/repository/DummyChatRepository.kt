//data.repository.DummyChatRepository
package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DummyChatRepository @Inject constructor() : ChatRepository {

    private var turnCount = 0
    private var dummySessionType = "WEEKLY" // 더미용 상태 변수

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {
        // 1. 가짜 로딩 (1초)
        delay(1000)
        turnCount++

        val dummyResponseText = if (endSession) {
            "상담을 종료합니다. (Dummy)"
        } else {
            "[$turnCount] 더미 응답입니다: '$text'"
        }

        // 2. ChatTurn 객체 생성
        val dummyTurn = ChatTurn(
            assistantMessage = ChatMessage.GuideMessage(dummyResponseText),
            isSessionEnded = endSession,
            currentWeek = 1,
            weekTitle = "더미 테스트 모드",
            weekGoals = listOf("더미 목표 1", "더미 목표 2")
        )

        return Result.success(dummyTurn)
    }

    // 새로운 세션 시작 (가짜 로직)
    override suspend fun startNewGeneralSession(): String {
        delay(500) // 살짝 로딩 흉내
        turnCount = 0 // 턴 초기화
        dummySessionType = "GENERAL" // 세션 타입 변경 흉내
        return "새로운 더미 상담이 시작되었습니다! (GENERAL 모드)"
    }

    // 현재 세션 타입 조회 (가짜 로직)
    override fun getCurrentSessionType(): String {
        return dummySessionType
    }

    // 과거 대화 내역 조회를 위한 threid 조회
    override fun getCurrentThreadId(): String? {
        // 더미라서 별도 스레드 개념 없음 → null
        return null
    }
}
