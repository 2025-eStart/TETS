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

        // 2. ChatTurn 객체 생성 (수정됨!)
        val dummyTurn = ChatTurn(
            assistantMessage = ChatMessage.GuideMessage(dummyResponseText),
            isSessionEnded = endSession,
            currentWeek = 1,
            weekTitle = "더미 테스트 모드",
            weekGoals = listOf("더미 목표 1", "더미 목표 2")
        )

        return Result.success(dummyTurn)
    }
}
