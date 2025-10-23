package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

////////////////// API 연동 없는 버전 //////////////////
@Singleton
class DummyChatRepository @Inject constructor() : ChatRepository {

    // 1. 대화 시나리오의 "단계"를 기억할 상태 변수
    private var conversationStep = 0

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {

        // API 호출을 흉내 내기 위한 1초 딜레이
        delay(1000)

        // 2. 사용자가 "종료"를 누르면, 시나리오와 관계없이 즉시 종료
        if (endSession) {
            conversationStep = 0 // (데모를 위해) 세션 리셋
            val endMessage = ChatMessage.GuideMessage("알겠어, 오늘 상담은 여기까지 하자! 수고했어.")
            val chatTurn = ChatTurn(
                assistantMessage = endMessage,
                isSessionEnded = true,
                homework = null
            )
            return Result.success(chatTurn)
        }

        // 3. (핵심) 사용자가 무엇을 입력하든(text), 정해진 시나리오대로 응답
        val replyMessage: ChatMessage
        var isEnded = false

        when (conversationStep) {
            // ViewModel의 init 메시지("...오늘 어떤 일이 있었니?")에 대한 첫 번째 응답
            0 -> {
                replyMessage = ChatMessage.GuideMessage("그렇구나, 쇼핑앱을 볼 때 기분이 어땠어?")
            }
            // "스트레스 풀렸어요" (예시)에 대한 두 번째 응답
            1 -> {
                replyMessage = ChatMessage.GuideMessage("스트레스가 풀리는 느낌이었구나. 혹시 쇼핑 말고 스트레스를 풀 수 있는 다른 방법이 있을까?")
            }
            // "산책?" (예시)에 대한 세 번째 응답 (세션 종료)
            2 -> {
                replyMessage = ChatMessage.GuideMessage("좋은 생각이야! 다음엔 쇼핑앱을 켜기 전에 10분 정도 가볍게 산책해보는 건 어때? (상담 종료)")
                isEnded = true // 챗봇이 대화를 종료시킴
            }
            // 3단계 이후의 모든 메시지 (세션이 이미 종료됨)
            else -> {
                replyMessage = ChatMessage.GuideMessage("오늘 상담은 종료되었어. 내일 또 얘기하자!")
                isEnded = true
            }
        }

        // 4. 다음 메시지를 위해 단계를 1 증가시킴
        if (isEnded) {
            // 세션이 종료되면, 다음 데모를 위해 단계를 리셋
            conversationStep = 0
        } else {
            conversationStep++
        }

        val chatTurn = ChatTurn(
            assistantMessage = replyMessage,
            isSessionEnded = isEnded,
            homework = null
        )

        return Result.success(chatTurn)
    }
}
